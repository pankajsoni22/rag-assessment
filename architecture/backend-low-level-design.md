# Backend Low-Level Design — Class Diagrams

This document drills into the backend modules defined in
[`architecture.md`](architecture.md) (the central architecture document —
see it first for the module boundaries, data flow, and design patterns this
file assumes) down to the class level. It is a **starting point, not a
contract**: attributes and method signatures will change as implementation
uncovers real requirements. What should stay stable is the shape —
which classes exist, what they depend on, and which boundaries are
interfaces.

Scope: the **backend tier only**. `VectorStore` appears here as the
interface the backend depends on; its Chroma-backed implementation belongs
to the storage tier and will be detailed when that tier's own phase spec is
written. API request/response DTOs are also out of scope here, per
`architecture.md`'s open item deferring exact endpoint/schema design —
the controllers below show intent and delegation, not final signatures.

---

## Domain Model

The types every service passes around. `Chunk`, `Document`, and
`DocumentSet` mirror the metadata fields already named in `architecture.md`
(`document_id`, `set_id`, `filename`, `format`, `uploaded_at`).

```mermaid
classDiagram
    class DocumentSet {
        +str id
        +str name
        +datetime created_at
    }

    class Document {
        +str id
        +str set_id
        +str filename
        +DocumentFormat format
        +IngestionStatus status
        +datetime uploaded_at
    }

    class DocumentFormat {
        <<enumeration>>
        PDF
        WORD
        TEXT
        MARKDOWN
    }

    class IngestionStatus {
        <<enumeration>>
        PROCESSING
        READY
        ERROR
    }

    class Chunk {
        +str id
        +str document_id
        +str set_id
        +str text
        +dict metadata
    }

    class RetrievedChunk {
        +Chunk chunk
        +float score
    }

    class Role {
        <<enumeration>>
        USER
        ASSISTANT
    }

    class ConversationTurn {
        +Role role
        +str content
        +datetime timestamp
    }

    class Citation {
        +str document_id
        +str filename
        +str chunk_id
    }

    class AnswerResult {
        +str answer
        +List~Citation~ citations
        +bool grounded
    }

    Document "1" --> "1" DocumentFormat
    Document "1" --> "1" IngestionStatus
    Document "1" o-- "*" Chunk : produces
    RetrievedChunk "1" --> "1" Chunk
    ConversationTurn "1" --> "1" Role
    AnswerResult "1" o-- "*" Citation
```

---

## Interfaces (Backend-Side Contracts)

```mermaid
classDiagram
    class DocumentLoader {
        <<interface>>
        +supports(format: DocumentFormat) bool
        +parse(file) str
    }

    class VectorStore {
        <<interface>>
        +upsert(chunks: List~Chunk~, vectors: List~Vector~) None
        +query(vector: Vector, filter: dict, top_k: int) List~RetrievedChunk~
        +delete(document_id: str) None
    }
```

`VectorStore` is implemented today by a Chroma-backed class that lives in
`project/storage/`; the backend only ever imports the interface.

---

## Ingestion Pipeline

Matches the *Strategy pattern* call-out in `architecture.md`: one
`DocumentLoader` implementation per format, selected through a registry so
adding a format never touches existing loader code.

```mermaid
classDiagram
    class DocumentLoader {
        <<interface>>
        +supports(format: DocumentFormat) bool
        +parse(file) str
    }
    class PDFLoader
    class WordLoader
    class TextLoader
    class MarkdownLoader
    DocumentLoader <|.. PDFLoader
    DocumentLoader <|.. WordLoader
    DocumentLoader <|.. TextLoader
    DocumentLoader <|.. MarkdownLoader

    class DocumentLoaderRegistry {
        -Dict~DocumentFormat, DocumentLoader~ loaders
        +register(format: DocumentFormat, loader: DocumentLoader) None
        +get_loader(format: DocumentFormat) DocumentLoader
    }
    DocumentLoaderRegistry o-- "many" DocumentLoader

    class ChunkingService {
        +chunk(text: str, document_id: str, set_id: str) List~Chunk~
    }

    class GeminiEmbeddingClient {
        +embed_texts(texts: List~str~) List~Vector~
    }

    class EmbeddingService {
        -GeminiEmbeddingClient client
        +embed(chunks: List~Chunk~) List~Vector~
    }
    EmbeddingService --> GeminiEmbeddingClient

    class VectorStore {
        <<interface>>
    }

    class DocumentSetService {
        -VectorStore vector_store
        +create_set(name: str) DocumentSet
        +list_sets() List~DocumentSet~
        +delete_set(set_id: str) None
        +add_document(set_id: str, file) Document
        +remove_document(document_id: str) None
        +list_documents(set_id: str) List~Document~
        +get_status(document_id: str) IngestionStatus
    }
    DocumentSetService --> VectorStore

    class IngestionService {
        -DocumentLoaderRegistry loader_registry
        -ChunkingService chunker
        -EmbeddingService embedder
        -VectorStore vector_store
        -DocumentSetService doc_set_service
        +ingest(file, set_id: str) Document
    }
    IngestionService --> DocumentLoaderRegistry
    IngestionService --> ChunkingService
    IngestionService --> EmbeddingService
    IngestionService --> VectorStore
    IngestionService --> DocumentSetService
```

---

## Query / RAG Pipeline

Matches the *Orchestrator pattern* call-out: `RAGOrchestrator` is the only
class aware of the full "answer a question" sequence. `RetrievalService`,
`GenerationService`, and `ConversationService` don't reference each other.

```mermaid
classDiagram
    class VectorStore {
        <<interface>>
    }

    class RetrievalService {
        -VectorStore vector_store
        -EmbeddingService embedder
        +retrieve(query: str, set_id: str, top_k: int) List~RetrievedChunk~
    }
    RetrievalService --> VectorStore

    class GroqClient {
        +complete(prompt: str) str
    }

    class GenerationService {
        -GroqClient client
        +generate(question: str, history: List~ConversationTurn~, chunks: List~RetrievedChunk~) AnswerResult
    }
    GenerationService --> GroqClient

    class ConversationService {
        -Dict~str, List~ConversationTurn~~ sessions
        +get_history(session_id: str) List~ConversationTurn~
        +append_turn(session_id: str, turn: ConversationTurn) None
    }

    class RAGOrchestrator {
        -ConversationService conversation_service
        -RetrievalService retrieval_service
        -GenerationService generation_service
        +answer_question(session_id: str, question: str, set_id: str) AnswerResult
    }
    RAGOrchestrator --> ConversationService
    RAGOrchestrator --> RetrievalService
    RAGOrchestrator --> GenerationService
```

---

## API Layer & Config

Controllers stay thin (*Service layer* pattern) — they translate HTTP to
service calls and back, with no business logic of their own. Shown here to
establish which service each controller depends on; exact routes and
request/response schemas are deferred, as noted in `architecture.md`.

```mermaid
classDiagram
    class DocumentController {
        -DocumentSetService doc_set_service
        +upload_document(file, set_id: str)
        +list_documents(set_id: str)
        +delete_document(document_id: str)
        +create_set(name: str)
        +list_sets()
        +delete_set(set_id: str)
    }
    DocumentController --> DocumentSetService

    class QueryController {
        -RAGOrchestrator orchestrator
        +ask(question: str, set_id: str, session_id: str)
    }
    QueryController --> RAGOrchestrator

    class Settings {
        +str groq_api_key
        +str google_api_key
        +str chroma_path
        +load()$ Settings
    }
```

`Settings` (the `Config` module in `architecture.md`) is loaded once at
startup and injected into `GeminiEmbeddingClient`, `GroqClient`, and
whichever storage-tier class constructs the Chroma client — never read ad
hoc from inside a service.

---

## Open Items

- Exact method signatures above are illustrative — parameter/return types
  will firm up once the backend is scaffolded (Phase 1 of
  `specs/002-master-development-plan.md`) and real framework types (e.g.
  FastAPI's `UploadFile`, LlamaIndex node types) are in play.
- API request/response DTOs, error/exception hierarchy, and pagination for
  list endpoints are not designed yet — deferred to the phase(s) that build
  the API layer and ingestion pipeline.
- Whether `EmbeddingService` is shared by reference between
  `IngestionService` and `RetrievalService` (single instance) or
  constructed separately is an implementation detail to settle during
  Phase 1 dependency wiring, not a design constraint here.
