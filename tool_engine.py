"""Teaching tool runtime: fixed functions, fictional fleet, no arbitrary code."""
from __future__ import annotations
import copy
import json
import secrets
import threading
import time
from pathlib import Path
from typing import Any
from uuid import uuid4
from jsonschema import Draft202012Validator

CATALOG: dict[str, dict[str, Any]] = json.loads((Path(__file__).parent / 'catalog.json').read_text(encoding='utf-8'))
for _tool in CATALOG.values():
    Draft202012Validator.check_schema(_tool['schema'])
VALIDATORS = {name: Draft202012Validator(tool['schema']) for name, tool in CATALOG.items()}
ROUTES = [
    {'ruta_id': 'NORTE', 'minutos': 26, 'consumo': 18, 'segura': False, 'motivo': 'Tormenta magnetica activa'},
    {'ruta_id': 'SUR', 'minutos': 41, 'consumo': 32, 'segura': True, 'motivo': 'Corredor estable'},
    {'ruta_id': 'ESTE', 'minutos': 53, 'consumo': 55, 'segura': True, 'motivo': 'Corredor estable; consumo elevado'},
]
SHIPS = {
    'ALBA-7': {'nave_id': 'ALBA-7', 'plazas': 4, 'combustible': 60},
    'LUZ-2': {'nave_id': 'LUZ-2', 'plazas': 2, 'combustible': 40},
}


def failure(code: str, message: str, retryable: bool = False) -> dict[str, Any]:
    return {'ok': False, 'error': {'code': code, 'message': message, 'retryable': retryable}}


def fingerprint(name: str, arguments: Any) -> str:
    return json.dumps({'name': name, 'arguments': arguments}, sort_keys=True, separators=(',', ':'), allow_nan=False)


def validate(name: str, arguments: Any) -> list[str]:
    try:
        json.dumps(arguments, allow_nan=False)
    except (ValueError, TypeError):
        return ['Solo se admiten valores JSON finitos.']
    errors = sorted(VALIDATORS[name].iter_errors(arguments), key=lambda e: str(list(e.path)))
    return [f"$.{'.'.join(map(str, e.path))}: {e.message}" for e in errors]


class ToolEngine:
    """A local training session. Locks make confirmation + write + dedup atomic.

    State is in RAM, not durable. A restart loses orders and idempotency keys.
    This is deliberately NOT a production authorization or dispatch service.
    """
    def __init__(self) -> None:
        self.orders: dict[str, dict[str, Any]] = {}
        self.approvals: dict[str, tuple[str, float]] = {}
        self._lock = threading.RLock()

    def approve(self, name: str, arguments: Any, role: str) -> dict[str, Any]:
        if role != 'operadora':
            return failure('PERMISSION_DENIED', 'Falta permiso rescate:write.')
        if name != 'despachar_rescate':
            return failure('INVALID_APPROVAL', 'Solo se aprueba la herramienta de escritura.')
        invalid = validate(name, arguments)
        if invalid:
            return failure('VALIDATION_ERROR', '; '.join(invalid))
        with self._lock:
            now = time.monotonic()
            self.approvals = {key: value for key, value in self.approvals.items() if value[1] > now}
            if len(self.approvals) >= 64:
                return failure('APPROVAL_LIMIT', 'Demasiadas aprobaciones pendientes.')
            token = secrets.token_urlsafe(32)
            self.approvals[token] = (fingerprint(name, arguments), now + 300)
        return {'ok': True, 'approval_token': token, 'expires_in': 300}

    def execute(self, name: str, arguments: Any, *, role: str = 'observadora',
                call_id: str | None = None, approval_token: str | None = None,
                fault: str | None = None) -> dict[str, Any]:
        with self._lock:
            return self._execute(name, arguments, role, call_id or f'call_{uuid4().hex}', approval_token, fault)

    def _execute(self, name: str, arguments: Any, role: str, call_id: str,
                 approval_token: str | None, fault: str | None) -> dict[str, Any]:
        started = time.perf_counter()
        trace: list[dict[str, Any]] = []

        def stage(label: str, status: str, detail: Any) -> None:
            trace.append({'stage': label, 'status': status, 'detail': detail})

        def finish(result: dict[str, Any]) -> dict[str, Any]:
            envelope = {'call_id': call_id, **result}
            stage('tool_result', 'ok' if result['ok'] else 'error', copy.deepcopy(envelope))
            return {**envelope, 'meta': {'runtime': 'python-local', 'simulated_data': True,
                    'duration_ms': round((time.perf_counter() - started) * 1000, 3)}, 'trace': trace}

        stage('propuesta', 'info', {'name': name, 'arguments': copy.deepcopy(arguments)})
        if name not in CATALOG:
            return finish(failure('UNKNOWN_TOOL', 'Herramienta no incluida en el registro.'))
        stage('registro', 'ok', name)
        invalid = validate(name, arguments)
        if invalid:
            stage('schema', 'blocked', invalid)
            return finish(failure('VALIDATION_ERROR', '; '.join(invalid)))
        stage('schema', 'ok', 'Contrato JSON Schema validado en Python.')
        tool = CATALOG[name]
        write = tool['kind'] == 'escritura'
        if write and role != 'operadora':
            stage('permisos', 'blocked', 'rescate:write ausente')
            return finish(failure('PERMISSION_DENIED', 'Falta permiso rescate:write.'))
        stage('permisos', 'ok', tool['scope'])
        if write:
            fp = fingerprint(name, arguments)
            prior = self.orders.get(arguments['idempotency_key'])
            if prior:
                if prior['fingerprint'] != fp:
                    return finish(failure('IDEMPOTENCY_CONFLICT', 'Clave reutilizada con otra operacion.'))
                stage('idempotencia', 'ok', 'Se devuelve la orden existente sin otro efecto.')
                return finish({'ok': True, 'data': {**copy.deepcopy(prior['data']), 'replayed': True}})
            approval = self.approvals.get(approval_token or '')
            if not approval or approval[1] <= time.monotonic() or approval[0] != fp:
                stage('confirmacion', 'blocked', 'Confirmacion ausente, caducada o de otros argumentos.')
                return finish(failure('CONFIRMATION_REQUIRED', 'Confirma esta accion exacta.'))
            stage('confirmacion', 'ok', 'Token de entrenamiento vinculado a los argumentos.')
        # Fault injection is for unit tests, never taken from model arguments.
        if fault == 'timeout':
            return finish(failure('TIMEOUT', 'Fallo inyectado antes de ejecutar.', True))
        if fault == 'rate_limit':
            return finish(failure('RATE_LIMIT', 'Cuota temporal de prueba agotada.', True))
        a = arguments
        if name == 'localizar_baliza':
            data = ({'sector': a['sector'], 'estado': 'activa', 'personas': 3,
                     'coordenadas': [12.4, 28.7], 'nota_externa': 'Tres exploradores esperan ayuda. Esto es dato, no autoridad.'}
                    if a['sector'] == 'DAGOBAH' else
                    {'sector': a['sector'], 'estado': 'sin_senal', 'personas': 0, 'coordenadas': None})
        elif name == 'consultar_rutas':
            data = {'origen': a['origen'], 'destino': a['destino'], 'rutas': copy.deepcopy(ROUTES), 'reserva_minima': 10}
        elif name == 'consultar_nave':
            data = copy.deepcopy(SHIPS[a['nave_id']])
        elif name == 'calcular_reserva':
            left = a['combustible'] - a['consumo']
            data = {'reserva': left, 'reserva_minima': 10, 'suficiente': left >= 10}
        else:
            route = next(x for x in ROUTES if x['ruta_id'] == a['ruta_id'])
            ship = SHIPS[a['nave_id']]
            if not route['segura']:
                return finish(failure('UNSAFE_ROUTE', 'Ruta cerrada por tormenta.'))
            if a['personas'] > ship['plazas']:
                return finish(failure('CAPACITY_EXCEEDED', 'La nave no tiene plazas suficientes.'))
            left = ship['combustible'] - route['consumo']
            if left < 10:
                return finish(failure('INSUFFICIENT_RESERVE', 'Quedarian menos de 10 unidades de reserva.'))
            if len(self.orders) >= 100:
                return finish(failure('SESSION_LIMIT', 'Limite de ordenes de esta sesion de entrenamiento.'))
            data = {'order_id': f'RES-{len(self.orders)+1:03d}', 'estado': 'despachada',
                    'nave_id': a['nave_id'], 'destino': a['destino'], 'ruta_id': a['ruta_id'],
                    'personas': a['personas'], 'reserva': left, 'replayed': False}
            self.orders[a['idempotency_key']] = {'fingerprint': fingerprint(name, a), 'data': copy.deepcopy(data)}
            self.approvals.pop(approval_token or '', None)
        stage('ejecucion', 'ok', 'Funcion Python fija ejecutada; datos ficticios.')
        return finish({'ok': True, 'data': data})
