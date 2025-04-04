from django.utils.deprecation import MiddlewareMixin
from .models import Agent


class AgentStatusMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.session.get('agent_username'):
            try:
                agent = Agent.objects.get(
                    username=request.session['agent_username'])
                if not agent.is_online:
                    agent.set_online()
            except Agent.DoesNotExist:
                pass
        else:
            agent_username = request.session.get('last_agent_username')
            if agent_username:
                try:
                    agent = Agent.objects.get(username=agent_username)
                    agent.set_offline()
                    del request.session['last_agent_username']
                except Agent.DoesNotExist:
                    pass

    def process_response(self, request, response):
        if request.session.get('agent_username'):
            request.session['last_agent_username'] = request.session['agent_username']
        return response
