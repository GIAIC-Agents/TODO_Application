from typing import List, Dict, Any
import json
from groq import Groq
from sqlmodel import Session
from ..services.mcp_tools import MCPTools
from ..models.chat import ChatRequest, ChatResponse
from ..config.settings import settings


class TodoAgent:
    def __init__(self):
        print(f"Initializing TodoAgent with Groq API key: {settings.groq_api_key[:20]}...")
        print(f"Using model: {settings.groq_model}")
        
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.groq_model
        self.mcp_tools = MCPTools()
    
    def get_system_prompt(self) -> str:
        return """You are a helpful todo assistant that manages tasks through natural language.

You have access to tools for managing tasks. When users speak naturally about tasks, use the appropriate tool:
- add_task: When they want to create a new task
- list_tasks: When they want to see their tasks  
- complete_task: When they want to mark a task as done
- delete_task: When they want to remove a task
- update_task: When they want to change a task

Examples:
- "buy milk" → use add_task with title "buy milk"
- "add groceries to my list" → use add_task with title "groceries"
- "show my tasks" → use list_tasks
- "what's on my list?" → use list_tasks
- "complete task 1" → use complete_task with task_id "1"
- "mark buy milk as done" → use complete_task with appropriate identifier
- "delete the first task" → use delete_task with task_id "1"
- "remove buy milk" → use delete_task with appropriate identifier
- "change task 1 to buy bread" → use update_task

Be natural and helpful!"""

    def get_tools_definition(self) -> List[Dict[str, Any]]:
        """Define tools for Groq function calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "add_task",
                    "description": "Create a new task in the todo list",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "The title/description of the task to add"
                            },
                            "description": {
                                "type": "string",
                                "description": "Optional longer description of the task"
                            }
                        },
                        "required": ["title"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_tasks",
                    "description": "Get all tasks from the todo list",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "complete_task",
                    "description": "Mark a task as completed",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "The ID or identifier of the task to complete"
                            }
                        },
                        "required": ["task_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_task",
                    "description": "Delete/remove a task from the list",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "The ID or identifier of the task to delete"
                            }
                        },
                        "required": ["task_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_task",
                    "description": "Update/modify a task's title or description",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "The ID of the task to update"
                            },
                            "title": {
                                "type": "string",
                                "description": "New title for the task"
                            },
                            "description": {
                                "type": "string",
                                "description": "New description for the task"
                            }
                        },
                        "required": ["task_id"]
                    }
                }
            }
        ]

    def execute_tool_call(self, session: Session, user_id: str, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call from Groq"""
        print(f"Executing tool: {tool_name} with args: {tool_args}")
        
        # Handle None tool_args
        if tool_args is None:
            tool_args = {}
        
        try:
            if tool_name == "add_task":
                return self.mcp_tools.add_task(
                    session, 
                    user_id, 
                    tool_args.get("title"),
                    tool_args.get("description")
                )
            
            elif tool_name == "list_tasks":
                # list_tasks doesn't need any parameters now
                return self.mcp_tools.list_tasks(session, user_id, "all")
            
            elif tool_name == "complete_task":
                return self.mcp_tools.complete_task(
                    session,
                    user_id,
                    tool_args.get("task_id")
                )
            
            elif tool_name == "delete_task":
                return self.mcp_tools.delete_task(
                    session,
                    user_id,
                    tool_args.get("task_id")
                )
            
            elif tool_name == "update_task":
                return self.mcp_tools.update_task(
                    session,
                    user_id,
                    tool_args.get("task_id"),
                    title=tool_args.get("title"),
                    description=tool_args.get("description")
                )
            
            else:
                return {"error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            print(f"Error executing tool {tool_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def _generate_response_from_tools(self, tool_calls: List[Dict[str, Any]]) -> str:
        """Generate user-friendly response from tool results"""
        if not tool_calls:
            return "I'm here to help you manage your tasks!"
        
        responses = []
        for call in tool_calls:
            tool_name = call["tool"]
            result = call["result"]
            
            if tool_name == "add_task":
                if "error" in result:
                    responses.append(f"❌ Failed to add task: {result['error']}")
                else:
                    responses.append(f"✅ Task '{result['title']}' has been added successfully!")
            
            elif tool_name == "list_tasks":
                if "error" in result:
                    responses.append(f"❌ Failed to list tasks: {result['error']}")
                elif result.get("tasks"):
                    task_list = "\n".join([
                        f"{'✅' if task.get('completed') else '⬜'} {i+1}. {task['title']}" 
                        for i, task in enumerate(result["tasks"])
                    ])
                    responses.append(f"📋 Your tasks:\n{task_list}")
                else:
                    responses.append("📋 You have no tasks yet.")
            
            elif tool_name == "delete_task":
                if "error" in result:
                    responses.append(f"❌ Failed to delete task: {result['error']}")
                else:
                    responses.append(f"🗑️ Task has been deleted successfully!")
            
            elif tool_name == "complete_task":
                if "error" in result:
                    responses.append(f"❌ Failed to complete task: {result['error']}")
                else:
                    responses.append(f"✅ Task '{result.get('title', '')}' marked as completed!")
            
            elif tool_name == "update_task":
                if "error" in result:
                    responses.append(f"❌ Failed to update task: {result['error']}")
                else:
                    responses.append(f"✏️ Task has been updated successfully!")
        
        return "\n\n".join(responses)

    def process_message(self, session: Session, user_id: str, message: str, conversation_history: List[Dict[str, str]]) -> ChatResponse:
        """Process user message using Groq function calling"""
        
        # Build conversation context
        messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ]
        
        # Add conversation history
        for msg in conversation_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        tool_calls_results = []
        
        try:
            print(f"Calling Groq API with function calling")
            print(f"Message: {message}")
            print(f"User ID: {user_id}")
            
            # Make Groq API call WITH tools/function calling
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.get_tools_definition(),
                tool_choice="auto"
            )
            
            assistant_message = response.choices[0].message
            
            # Check if AI wants to call tools
            if assistant_message.tool_calls:
                print(f"AI requested {len(assistant_message.tool_calls)} tool calls")
                
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    # Execute the tool
                    result = self.execute_tool_call(session, user_id, tool_name, tool_args)
                    
                    tool_calls_results.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "result": result
                    })
                
                # Generate friendly response from tool results
                final_response = self._generate_response_from_tools(tool_calls_results)
            else:
                # No tool calls, just return the AI's text response
                final_response = assistant_message.content or "I'm here to help!"
            
            return ChatResponse(
                conversation_id=None,
                response=final_response,
                tool_calls=tool_calls_results
            )
            
        except Exception as e:
            print(f"Error in TodoAgent.process_message: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            
            return ChatResponse(
                conversation_id=None,
                response=f"Sorry, I encountered an error: {str(e)}",
                tool_calls=[]
            )
