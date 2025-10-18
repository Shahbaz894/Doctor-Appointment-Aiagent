from typing import Literal, List, Any
from langchain_core.tools import tool
from langgraph.types import Command
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict, Annotated
from langchain_core.prompts.chat import ChatPromptTemplate
from langgraph.graph import START, StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from prompt_library.prompt import System_prompt
from utilis.llms import LLMModel
from toolkit.toolkit import *
from logger.logging import logger


class Router(TypedDict):
    next: Literal["information_node", "booking_node", "FINISH"]
    reasoning: str


class AgentState(TypedDict):
    message: Annotated[list[Any], add_messages]
    id_number: str
    next: str
    query: str
    current_reasoning: str


class DoctorAppointmentAgent:
    def __init__(self):
        llm = LLMModel()
        self.llm_model = llm.get_model()
        logger.info("LLM model initialized successfully.")

    def supervisor_node(self, state: AgentState) -> Command[Literal['information_node', 'booking_node', '__end__']]:
        logger.info("Entered supervisor node.")
        messages = [
            {"role": "system", "content": System_prompt},
            {"role": "user", "content": f"user's identification number is {state['id_number']}"},
        ] + state["message"]

        query = ''
        if len(state['message']) == 1:
            query = state["message"][0].content

        response = self.llm_model.with_structured_output(Router).invoke(messages)
        goto = response['next']
        logger.info(f"Supervisor decision: {goto}")

        if goto == 'FINISH':
            goto = END

        update_data = {
            'next': goto,
            'current_reasoning': response["reasoning"]
        }

        if query:
            update_data.update({
                'query': query,
                'messages': [HumanMessage(content=f"user's identification number is {state['id_number']}")]
            })

        return Command(goto=goto, update=update_data)

    def information_node(self, state: AgentState) -> Command[Literal['supervisor']]:
        logger.info("Entered information node.")
        system_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a specialized agent to provide information related to availability of doctors or any FAQs related to the hospital. Use tools and always assume current year is 2024."),
            ("placeholder", "{messages}")
        ])

        information_agent = create_react_agent(
            model=self.llm_model,
            tools=[check_availability_by_doctor, check_availability_by_specialization],
            prompt=system_prompt
        )

        result = information_agent.invoke(state)

        return Command(
            update={
                "messages": state["message"] + [
                    AIMessage(content=result["messages"][-1].content, name="information_node")
                ]
            },
            goto="supervisor"
        )

    def booking_node(self, state: AgentState) -> Command[Literal['supervisor']]:
        logger.info("Entered booking node.")
        system_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a specialized agent to handle appointment booking, cancellation, or rescheduling. Use tools and assume the year is 2024."),
            ("placeholder", "{messages}")
        ])

        booking_agent = create_react_agent(
            model=self.llm_model,
            tools=[set_appointment, cancel_appointment, reschedule_appointment],
            prompt=system_prompt
        )

        result = booking_agent.invoke(state)

        return Command(
            update={
                "messages": state["message"] + [
                    AIMessage(content=result["messages"][-1].content, name="booking_node")
                ]
            },
            goto="supervisor"
        )

    def workflow(self):
        logger.info("Building workflow graph.")
        self.graph = StateGraph(AgentState)
        self.graph.add_node("supervisor", self.supervisor_node)
        self.graph.add_node("information_node", self.information_node)
        self.graph.add_node("booking_node", self.booking_node)
        self.graph.add_edge(START, "supervisor")
        self.app = self.graph.compile()
        logger.info("Workflow graph compiled.")
        return self.app
