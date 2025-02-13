from flask import Flask, request, jsonify
from .agent_registry import AgentRegistry
from .services.workflow import WorkflowService
from .models.message import Message
from .models.agent import Agent
from contextlib import asynccontextmanager
import asyncio

app = Flask(__name__)
agent_registry = AgentRegistry()
workflow_service = WorkflowService(agent_registry)

@app.route('/message', methods=['POST'])
def handle_message():
    """处理用户消息"""
    data = request.json
    message = Message(
        user_id=data['user_id'],
        content=data['content'],
        session_id=data.get('session_id')
    )

    try:
        result = workflow_service.process_message(message)
        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/agent/register', methods=['POST'])
def register_agent():
    """注册智能体"""
    data = request.json
    agent = Agent(
        name=data['name'],
        type=data['type'],
        endpoints=data['endpoints'],
        properties=data.get('properties', {})
    )

    try:
        agent_registry.register(agent)
        return jsonify({"status": "success", "message": "Agent registered successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/agent/unregister', methods=['POST'])
def unregister_agent():
    """注销智能体"""
    data = request.json
    agent_name = data['name']

    try:
        agent_registry.unregister(agent_name)
        return jsonify({"status": "success", "message": "Agent unregistered successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.teardown_appcontext
def shutdown_session(exception=None):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(workflow_service.close())
    loop.close()

if __name__ == '__main__':
    app.run(debug=True)