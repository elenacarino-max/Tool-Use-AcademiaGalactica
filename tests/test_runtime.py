import copy
from concurrent.futures import ThreadPoolExecutor
import pytest
from tool_engine import ToolEngine, CATALOG

@pytest.fixture
def engine():
    return ToolEngine()

def arguments():
    return copy.deepcopy(CATALOG['despachar_rescate']['example'])

@pytest.mark.parametrize('name', list(CATALOG))
def test_contracts_are_valid(name):
    from tool_engine import validate
    assert validate(name, CATALOG[name]['example']) == []

@pytest.mark.parametrize('value', [{}, {'sector': 42}, {'sector': 'DAGOBAH', 'admin': True},
                                  {'sector': ''}, {'sector': 'CORUSCANT'}, None, [], True])
def test_invalid_args(engine, value):
    assert engine.execute('localizar_baliza', value)['error']['code'] == 'VALIDATION_ERROR'

@pytest.mark.parametrize('name', ['__proto__', 'constructor', 'toString', 'eval', 'anything'])
def test_allowlist(engine, name):
    assert engine.execute(name, {})['error']['code'] == 'UNKNOWN_TOOL'

def test_calculation(engine):
    assert engine.execute('calcular_reserva', {'combustible': 60, 'consumo': 32})['data']['reserva'] == 28

@pytest.mark.parametrize('bad', ['60', True, float('inf'), float('nan')])
def test_no_coercion_or_nonfinite(engine, bad):
    assert engine.execute('calcular_reserva', {'combustible': bad, 'consumo': 32})['error']['code'] == 'VALIDATION_ERROR'

def test_read_mode_no_write(engine):
    assert engine.execute('despachar_rescate', arguments())['error']['code'] == 'PERMISSION_DENIED'

def test_operator_needs_confirmation(engine):
    assert engine.execute('despachar_rescate', arguments(), role='operadora')['error']['code'] == 'CONFIRMATION_REQUIRED'

def test_bound_confirmation(engine):
    a = arguments()
    p = engine.approve('despachar_rescate', a, 'operadora')
    a['ruta_id'] = 'ESTE'
    assert engine.execute('despachar_rescate', a, role='operadora', approval_token=p['approval_token'])['error']['code'] == 'CONFIRMATION_REQUIRED'

def test_expired_confirmation(engine):
    a = arguments()
    p = engine.approve('despachar_rescate', a, 'operadora')
    fp, _ = engine.approvals[p['approval_token']]
    engine.approvals[p['approval_token']] = (fp, 0)
    assert engine.execute('despachar_rescate', a, role='operadora', approval_token=p['approval_token'])['error']['code'] == 'CONFIRMATION_REQUIRED'

@pytest.mark.parametrize('key,value,code', [('ruta_id','NORTE','UNSAFE_ROUTE'), ('ruta_id','ESTE','INSUFFICIENT_RESERVE'), ('nave_id','LUZ-2','CAPACITY_EXCEEDED')])
def test_business_rules(engine, key, value, code):
    a = arguments()
    a[key] = value
    p = engine.approve('despachar_rescate', a, 'operadora')
    assert engine.execute('despachar_rescate', a, role='operadora', approval_token=p['approval_token'])['error']['code'] == code
    assert not engine.orders

def test_idempotency(engine):
    a = arguments()
    p = engine.approve('despachar_rescate', a, 'operadora')
    one = engine.execute('despachar_rescate', a, role='operadora', approval_token=p['approval_token'], call_id='first')
    two = engine.execute('despachar_rescate', a, role='operadora', call_id='second')
    assert one['data']['order_id'] == two['data']['order_id']
    assert two['data']['replayed'] is True
    assert two['call_id'] == 'second'
    assert len(engine.orders) == 1
    a['personas'] = 2
    assert engine.execute('despachar_rescate', a, role='operadora')['error']['code'] == 'IDEMPOTENCY_CONFLICT'

def test_idempotency_concurrent(engine):
    a = arguments()
    p = engine.approve('despachar_rescate', a, 'operadora')
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda _: engine.execute('despachar_rescate', a, role='operadora', approval_token=p['approval_token']), range(12)))
    assert all(x['ok'] for x in results)
    assert len(engine.orders) == 1
    assert sum(not x['data']['replayed'] for x in results) == 1

def test_timeout_before_write(engine):
    a = arguments()
    p = engine.approve('despachar_rescate', a, 'operadora')
    result = engine.execute('despachar_rescate', a, role='operadora', approval_token=p['approval_token'], fault='timeout')
    assert result['error']['retryable'] is True
    assert not engine.orders
    assert engine.execute('despachar_rescate', a, role='operadora', approval_token=p['approval_token'])['ok']
