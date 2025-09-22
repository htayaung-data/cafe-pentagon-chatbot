# RAG Integration Request for Backend Team

## Overview
We need to integrate RAG (Retrieval-Augmented Generation) capabilities into our HITL (Human-in-the-Loop) admin panel system. This document outlines our requirements and requests information about your existing RAG infrastructure.

## Current System Architecture

### Admin Panel (Frontend)
- **Technology**: Next.js, TypeScript, Tailwind CSS
- **Purpose**: HITL management interface for human agents
- **Current Status**: Basic HITL functionality implemented, RAG integration needed

### Backend RAG Service
- **Technology**: LangGraph, Pinecone, Supabase, Railway, Node.js
- **Purpose**: Full RAG implementation for chatbot responses
- **Current Status**: Active and serving conversation page

### Database Schema
```sql
-- Key fields in conversations table
rag_enabled boolean not null default true
human_handling boolean not null default false
```

## Our Vision: RAG as Knowledge Assistant in HITL

### Current Flow (Conversation Page)
```
FB User Question → RAG Chatbot → Direct Response to User
Conditions: human_handling = FALSE, rag_enabled = TRUE
```

### Desired Flow (HITL Page)
```
FB User Question → RAG Service → Quick Reply Suggestions → Admin Panel → Human Selects/Edits → Human Sends
Conditions: human_handling = TRUE, rag_enabled = TRUE
```

### Alternative Flow (HITL Page - No RAG)
```
FB User Question → No RAG → Human Responds Manually
Conditions: human_handling = TRUE, rag_enabled = FALSE
```

## Key Requirements

### 1. Conditional RAG Behavior
- **When** `human_handling = FALSE` AND `rag_enabled = TRUE`: RAG responds directly to user
- **When** `human_handling = TRUE` AND `rag_enabled = TRUE`: RAG generates suggestions for admin panel (NOT sent to user)
- **When** `human_handling = TRUE` AND `rag_enabled = FALSE`: No RAG assistance

### 2. RAG Suggestions Format
- **Quick Reply Options**: 2-3 contextually relevant response suggestions
- **Knowledge Documents**: Relevant policies, FAQs, documents
- **Key Facts**: Extracted information points
- **Suggested Response**: Complete response template for human editing

### 3. Integration Points
- **Real-time Updates**: RAG suggestions when new FB messages arrive in HITL
- **API Endpoint**: New endpoint for HITL RAG assistance
- **Authentication**: Secure communication between admin panel and RAG service

## Questions for Backend Team

### System Design Questions
1. **Current RAG Architecture**: How is your RAG service currently structured? What components handle document retrieval, embedding, and response generation?

2. **Existing Endpoints**: What RAG-related API endpoints do you currently have? Can they be extended for HITL use?

3. **Conversation Context**: How does your RAG service currently access conversation history and user context?

4. **Document Storage**: How are documents stored and indexed? What's the retrieval mechanism?

### Integration Approach Questions
1. **Flag Checking**: How can we implement the conditional logic (`human_handling` + `rag_enabled`) in your system?

2. **New Endpoint Design**: What would be the optimal API design for the HITL RAG assistance endpoint?

3. **Real-time Communication**: How do you recommend handling real-time updates between RAG service and admin panel?

4. **Performance Considerations**: What are the performance implications of adding HITL RAG assistance?

### Technical Questions
1. **Authentication**: How should we handle authentication between admin panel and RAG service?

2. **Error Handling**: What error handling and fallback mechanisms should we implement?

3. **Rate Limiting**: Are there any rate limiting considerations for HAG requests?

4. **Monitoring**: How can we monitor and track RAG usage in HITL mode?

## Requested Deliverables

Please provide a `.md` file that includes:

1. **System Architecture Overview**: High-level design of your RAG service
2. **Current API Structure**: Existing endpoints and their purposes
3. **Integration Recommendations**: How to implement the conditional RAG behavior
4. **New Endpoint Design**: Proposed API design for HITL RAG assistance
5. **Implementation Steps**: Recommended approach and timeline
6. **Technical Considerations**: Performance, security, and scalability factors

## Important Notes

- **No Code Required**: We only need system design and approach documentation
- **Focus on Integration**: How to connect existing RAG service with HITL requirements
- **Scalability**: Consider future enhancements and additional HITL features
- **Performance**: Ensure RAG suggestions are generated quickly for human agents

## Timeline
- **Documentation Request**: ASAP
- **Review & Discussion**: After receiving your response
- **Implementation Planning**: Based on your recommendations

## Contact
Please provide your response as a `.md` file. We can schedule a follow-up discussion to clarify any questions or discuss implementation details.

---

**Goal**: Enable human agents in HITL to leverage RAG as a knowledge assistant while maintaining full human control over responses.
