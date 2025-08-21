# HITL Admin Panel Implementation Guide

## Overview
This document outlines the implementation requirements for the Human-in-the-Loop (HITL) Admin Panel, focusing on two main pages: Conversation Page and HITL Page. The system enables human staff to monitor, intervene, and manage chatbot conversations that require human attention.

## System Architecture

### Core Principles
- **Clear Separation**: Conversation Page shows available conversations, HITL Page shows conversations under human control
- **Single Admin Workflow**: One admin per conversation (expandable to multiple admins later)
- **Manual Control**: Admins manually decide when to release conversations back to the bot
- **Real-time Updates**: Live escalation alerts and conversation status changes
- **Resolution Tracking**: Comprehensive tracking of conversation resolution status

## Conversation Page Implementation

### Purpose
Display all conversations that are not currently under human control, with filtering capabilities to identify conversations requiring human intervention.

### Core Features

#### 1. Conversation List Display
- Show all conversations where `human_handling = false`
- Display conversation metadata: user ID, platform, status, priority, message count
- Real-time updates when conversation status changes
- Pagination for large conversation volumes

#### 2. Smart Filtering System
- **Human Requirement Filter**: Show conversations with messages where `requires_human = true`
- **Status Filter**: Filter by conversation status (active, escalated, resolved, closed)
- **Priority Filter**: Filter by priority levels 1-5
- **Platform Filter**: Filter by communication platform (Facebook, Messenger, etc.)
- **Time Filter**: Filter by last message timestamp ranges
- **RAG Status Filter**: Filter by whether RAG is enabled or disabled

#### 3. Conversation Information Display
- **Basic Info**: Conversation ID, user ID, platform, creation date
- **Current Status**: Status, priority, RAG enabled/disabled
- **Message Summary**: Total message count, count of messages requiring human attention
- **Escalation History**: Previous escalation reasons and timestamps
- **Last Activity**: Timestamp of last message or activity

#### 4. Quick Action Buttons
- **Take Responsibility**: Assign conversation to current admin and move to HITL page
- **Escalate**: Mark conversation as escalated with reason
- **Set Priority**: Change conversation priority level
- **Toggle RAG**: Enable or disable RAG for the conversation
- **View Details**: Open detailed conversation view

#### 5. Visual Indicators
- **Priority Badges**: Color-coded priority levels (1-5)
- **Escalation Alerts**: Visual indicators for escalated conversations
- **Human Requirement Count**: Number of messages needing human attention
- **RAG Status**: Visual indicator for RAG enabled/disabled state

### Technical Requirements
- Real-time subscription to conversation table changes
- Efficient filtering and search capabilities
- Responsive design for different screen sizes
- Optimized pagination for performance

## HITL Page Implementation

### Purpose
Display and manage conversations currently under human control, providing tools for resolution and release back to the bot system.

### Core Features

#### 1. HITL Dashboard Header
- **Active HITL Count**: Total conversations with `human_handling = true`
- **Assigned to Me**: Conversations assigned to current admin
- **Escalation Alerts**: Count of conversations exceeding time thresholds
- **Priority Queue**: High-priority conversations requiring immediate attention

#### 2. Conversation Queue Management
- **Assigned Conversations**: Show conversations assigned to current admin
- **Priority Sorting**: Sort by priority level (highest first)
- **Time-based Escalation**: Visual indicators for conversations in HITL for extended periods
- **Status Overview**: Quick view of conversation resolution progress

#### 3. Conversation Assignment System
- **Current Assignment**: Display which admin is handling each conversation
- **Workload Management**: Show admin's current conversation count
- **Assignment History**: Track conversation assignment changes

#### 4. Admin Reply Interface
- **Rich Text Editor**: Support for formatted text, emojis, and basic markdown
- **Quick Reply Templates**: Pre-written responses for common scenarios
- **Message Context**: Display full conversation history with human requirement highlights
- **Language Support**: Multi-language reply capability
- **File Attachments**: Support for images and documents if needed

#### 5. Resolution Management System
- **Resolution Status Options**:
  - **Fully Resolved**: All issues addressed, ready to return to bot
  - **Partially Resolved**: Some issues addressed, but conversation needs continued human attention
  - **Not Resolved**: Issues remain, conversation requires escalation or transfer
- **Resolution Notes**: Required field for documenting resolution details
- **Resolution Timestamp**: Automatic tracking of when resolution was marked

#### 6. Conversation Release Workflow
- **Release to Bot**: Return conversation to automated handling
- **Release with Notes**: Include resolution summary and notes
- **Partial Release**: Release specific resolved issues while keeping others in HITL
- **Escalation Transfer**: Transfer to supervisor or specialized team

#### 7. Time-based Escalation Features
- **24-Hour Alert**: Visual warning for conversations in HITL for over 24 hours
- **48-Hour Critical**: Enhanced warning for conversations exceeding 48 hours
- **Escalation Filtering**: Filter conversations by escalation time thresholds
- **Automatic Notifications**: Real-time alerts for time-based escalations

#### 8. HITL Analytics & Insights
- **Resolution Time Tracking**: Average time to resolve different types of issues
- **Admin Performance Metrics**: Response time, resolution rate, conversation volume
- **Common Issue Patterns**: Most frequent escalation reasons and resolution types
- **Platform Performance**: Resolution metrics across different communication platforms

### Technical Requirements
- Real-time updates for conversation status changes
- Efficient conversation filtering and sorting
- Rich text editing capabilities
- File upload and management system
- Comprehensive audit logging

## Real-time Implementation Requirements

### Escalation Alerts
- **Immediate Notifications**: Real-time alerts when conversations are escalated
- **Time-based Alerts**: Automatic alerts at 24-hour and 48-hour thresholds
- **Visual Indicators**: Clear visual cues for escalation status
- **Sound Notifications**: Optional audio alerts for critical escalations

### Live Updates
- **Conversation Status**: Real-time updates when conversation status changes
- **Message Updates**: Live updates when new messages arrive
- **Assignment Changes**: Immediate notification of conversation assignment changes
- **Resolution Updates**: Real-time updates when resolution status changes

## Resolution Tracking System

### Resolution Status Workflow
1. **Admin Takes Responsibility**: Conversation moves to HITL page
2. **Work in Progress**: Admin works on resolving issues
3. **Resolution Assessment**: Admin evaluates resolution status
4. **Status Update**: Admin marks conversation with appropriate resolution status
5. **Release Decision**: Admin decides whether to release or continue working

### Resolution Documentation
- **Required Fields**: Resolution status, detailed notes, resolution timestamp
- **Optional Fields**: Internal notes, escalation reasons, follow-up requirements
- **Audit Trail**: Complete history of resolution attempts and outcomes
- **Quality Metrics**: Tracking of resolution effectiveness and user satisfaction

## Database Schema Requirements

### Conversation Table Fields
- `human_handling`: Boolean flag for HITL status
- `status`: Current conversation status
- `priority`: Priority level (1-5)
- `assigned_admin_id`: Admin currently handling the conversation
- `escalation_reason`: Reason for escalation
- `escalation_timestamp`: When escalation occurred
- `rag_enabled`: RAG system status
- `last_message_at`: Last activity timestamp
- `last_admin_activity`: Last admin interaction timestamp
- `admin_notes`: Internal admin notes and observations

### Message Table Fields
- `requires_human`: Boolean flag for human attention requirement
- `human_replied`: Boolean flag for human response
- `sender_type`: Message sender type (user, bot, human)
- `confidence_score`: Bot confidence level
- `metadata`: Additional context and information

### Admin Actions Table
- `conversation_id`: Reference to conversation
- `admin_id`: Admin performing the action
- `action_type`: Type of action performed
- `details`: Action-specific information
- `timestamp`: When action occurred
- `resolution_status`: Resolution outcome
- `resolution_notes`: Detailed resolution documentation

## User Experience Requirements

### Interface Design
- **Intuitive Navigation**: Clear distinction between Conversation and HITL pages
- **Responsive Layout**: Works effectively on desktop, tablet, and mobile devices
- **Accessibility**: Support for screen readers and keyboard navigation
- **Theme Support**: Light and dark theme options

### Performance Requirements
- **Fast Loading**: Page load times under 2 seconds
- **Smooth Interactions**: Responsive interface with minimal lag
- **Efficient Filtering**: Filter results update in real-time
- **Optimized Pagination**: Handle large conversation volumes efficiently

### Security Requirements
- **Authentication**: Secure admin login and session management
- **Authorization**: Role-based access control
- **Audit Logging**: Complete audit trail of all admin actions
- **Data Protection**: Secure handling of sensitive conversation data

## Implementation Phases

### Phase 1: Core Functionality
- Basic Conversation and HITL page layouts
- Essential filtering and sorting capabilities
- Basic admin actions (take responsibility, release)
- Simple resolution status tracking

### Phase 2: Enhanced Features
- Real-time updates and notifications
- Advanced filtering and search capabilities
- Rich text editing and file attachments
- Comprehensive resolution tracking

### Phase 3: Analytics and Optimization
- Performance analytics and insights
- Advanced escalation management
- Workflow optimization features
- Multi-admin support preparation

## Success Metrics

### Performance Indicators
- **Response Time**: Average time from escalation to admin response
- **Resolution Rate**: Percentage of conversations successfully resolved
- **User Satisfaction**: Feedback on resolution quality
- **System Uptime**: Admin panel availability and reliability

### Quality Metrics
- **Resolution Accuracy**: Correctness of issue identification and resolution
- **Admin Efficiency**: Time spent per conversation and resolution
- **Escalation Reduction**: Decrease in unnecessary escalations
- **User Experience**: Improvement in overall conversation quality

## Key Implementation Considerations

### State Management
- Clear conversation state transitions between pages
- Consistent data synchronization across components
- Efficient real-time update handling
- Proper error handling and recovery

### Data Flow
- Real-time data updates from Supabase
- Optimistic UI updates for better user experience
- Efficient data caching and pagination
- Proper data validation and sanitization

### Integration Points
- Supabase real-time subscriptions
- Admin authentication and authorization
- Facebook Messenger API integration
- Audit logging and monitoring systems

This implementation guide provides a comprehensive framework for building a professional-grade HITL admin panel that meets industry standards while maintaining simplicity and efficiency for your team.
