# Smart Travel Companion – Architecture Document

This document outlines the architecture and design decisions behind the Context-Aware AI Layer prototype, focusing on Memory Design, Orchestration, Context Switching, Invalidation strategies, and Scalability.

## 1. Memory Design & Context Model
**Strategy:** We employ a deeply structured state model divided into discrete context "buckets".

* **Data Storage Mechanism:** Memory is managed by LangGraph's persistent state mechanism via `MemorySaver`. This bounds state objects per user conversation mapping (`session_id`).
* **Session-Level Memory:** Includes linear conversation logs (`messages`) managed by Langchain's message reducers, and `active_service` denoting the intent cursor.
* **Service-Specific Context Buckets:**
  Each specialized travel service owns a structured Pydantic schema tracking discrete dimensions. For example:
  * `FlightContext` stores tracking details (origin, destination, dates, passengers), search state results (`results`), selection indicators (`selected_flight_id`, `passenger_details`), and macro flow tracking (`flow_state`).
  * `HotelContext` similarly tracks variables required for hotels (city, checks_in/out, guests, etc.).

By strictly binding LLM intent outputs to these Pydantic formats via `with_structured_output`, we guarantee high-fidelity extraction without relying strictly on semantic prompt-parsing. 

## 2. State Machine & Orchestration Logic
**Strategy:** We orchestrate via a LangGraph DAG (Directed Acyclic Graph) routing architecture.

1. **Router Node (`route_request`):** Acts as the ingress gateway. The model interprets the human payload, considers the current `active_service`, and maps the intent to the corresponding node logic (`flight_agent` vs `hotel_agent`).
2. **Sub-Nodes (Agents):** 
   * When handling a specific service, the active sub-agent focuses *solely* on its context bucket.
   * State is decoupled dynamically: The agent prompts the user until fields are complete (`flow_state: search`), invokes mock external tools to fetch data, caches tools responses to (`results`), shifts to (`flow_state: verify`), tracks follow-up Q&A, and proceeds to user-selection and (`flow_state: book`).

## 3. Slot Tracking Approach
**Strategy:** Implicit structured extraction.
* Instead of rigid rule-based prompt flow schemas ("If no origin, ask origin"), we feed the current Pydantic schema state into the LLM system prompt alongside instructions.
* The system invokes Gemini 2.5 Flash equipped with the extraction schema (`FlightExtraction` / `HotelExtraction`). The LLM fills the empty fields (slots) naturally from language and optionally returns a conversational string guiding the user to the next missing component. 
* Once slots are complete for a service step, Python logic executes the necessary transition to API call wrappers.

## 4. Context Switching Strategy
**Strategy:** Deterministic routing mapping and isolated buckets.
* **Preserving Contexts:** Since contexts are physically segregated (`AppState.flight_context` and `AppState.hotel_context`), switching from flight interaction to hotel interaction leaves the in-progress `flight_context` utterly untouched in the session threads (in `MemorySaver`).
* **Avoiding Data Leakage:** Sub-agents only extract parameters targeting their schema bounds, avoiding the cross-pollution common in naive chat systems. 
* **Resuming:** If a user jumps back to flights ("Wait let's finish the flight"), the *Router* flags `active_service = flight`. The Flight Agent resumes using the frozen `flight_context` retaining exact progress accurately and resolving.

## 5. Invalidation & Reconfirmation Logic
**Strategy:** Dependency-graph validation hook.
* When evaluating an intent transition, the Python sub-agent receives previously unedited context from LangGraph, and new context populated from Gemini.
* Custom invalidation blocks inspect for mutations. 
   *(e.g., if `new_extraction.origin != current_state.origin`)*
* If core dependency mutations occur, the agent force patches the state tree:
   * clears `results`.
   * clears `selected_flight_id`.
   * rolls `flow_state` backward from 'book/verify' to 'search'.
* This implicitly invalidates cascaded assumptions correctly without confusing the LLM.

## 6. Scalability Assessment (Optional Extras)

- **10-15 Services Expansion:** The Router node dynamically accepts enum additions (Rental_car, Activities, Transit). By separating context tracking per node cleanly, horizontal scalability logic behaves neutrally up to infinite modules without degrading LLM cross-polluted contexts.
- **Context Compression Strategies:** Lengthy session `messages` arrays create context limits. We could intercept message persistence on the `add_messages` reducer to periodically execute a `Summarization Node`, condensing long histories while treating `AppState` Pydantic objects as the primary source of truth.
- **Production Orchestration Engine:** Moving towards deploying individual APIs as microservices on AWS/GCP, `LangGraph` translates natively into serverless orchestrations (like Temporal IO, AWS Step Functions) where Node state executions correspond to independent container tasks querying the central `Redis` bounded Session Memory Database.
- **Tool Routing Logic:** Extending the sub-agents so they can iteratively loop through standard LangChain `ToolNodes` fetching live GDS flight systems (Amadeus, Sabre).
