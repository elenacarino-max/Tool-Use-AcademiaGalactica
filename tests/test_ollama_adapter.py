import json
import httpx
from ollama_readonly import run_agent

def test_read_tool_loop_with_mock_provider():
    requests = []
    def handler(request):
        data = json.loads(request.content)
        requests.append(data)
        if len(requests) == 1:
            return httpx.Response(200, json={'message':{'role':'assistant','content':'','tool_calls':[{'function':{'name':'localizar_baliza','arguments':{'sector':'DAGOBAH'}}}]}})
        assert data['messages'][-2]['role'] == 'assistant'
        assert data['messages'][-1]['role'] == 'tool'
        assert json.loads(data['messages'][-1]['content'])['data']['personas'] == 3
        return httpx.Response(200, json={'message':{'role':'assistant','content':'Hay tres exploradores.'}})
    with httpx.Client(base_url='http://127.0.0.1:11434', transport=httpx.MockTransport(handler)) as c:
        result = run_agent('Consulta Dagobah','modelo-de-prueba',c)
    assert result['ok'] and result['answer'] == 'Hay tres exploradores.'
    assert len(result['tool_events']) == 1
    assert all(t['function']['name'] != 'despachar_rescate' for t in requests[0]['tools'])

def test_model_cannot_use_write_tool():
    def handler(request):
        return httpx.Response(200, json={'message':{'role':'assistant','tool_calls':[{'function':{'name':'despachar_rescate','arguments':{}}}]}})
    with httpx.Client(base_url='http://127.0.0.1:11434',transport=httpx.MockTransport(handler)) as c:
        result = run_agent('Haz algo','modelo-de-prueba',c,max_calls=2)
    assert result['error']['code'] == 'BUDGET_EXCEEDED'
    assert len(result['tool_events']) == 2
    assert all(e['result']['error']['code'] == 'UNKNOWN_TOOL' for e in result['tool_events'])

def test_invalid_arguments_return_controlled_result():
    counter = 0
    def handler(request):
        nonlocal counter
        counter += 1
        if counter == 1:
            return httpx.Response(200,json={'message':{'role':'assistant','tool_calls':[{'function':{'name':'localizar_baliza','arguments':'not-json'}}]}})
        return httpx.Response(200,json={'message':{'role':'assistant','content':'No pude ejecutar la consulta.'}})
    with httpx.Client(base_url='http://127.0.0.1:11434',transport=httpx.MockTransport(handler)) as c:
        result = run_agent('Consulta','modelo-de-prueba',c)
    assert result['tool_events'][0]['result']['error']['code'] == 'VALIDATION_ERROR'
