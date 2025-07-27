-- Supabase Database Schema for Cafe Pentagon Chatbot
-- Run this in your Supabase SQL Editor

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- User Profiles Table
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    facebook_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    source VARCHAR(50) DEFAULT 'facebook_messenger',
    status VARCHAR(20) DEFAULT 'active',
    
    -- Facebook Profile Data
    facebook_name VARCHAR(255),
    facebook_first_name VARCHAR(255),
    facebook_last_name VARCHAR(255),
    facebook_profile_pic TEXT,
    facebook_locale VARCHAR(10),
    facebook_timezone INTEGER,
    facebook_gender VARCHAR(20),
    
    -- Contact Information
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    
    -- Preferences (stored as JSON)
    preferences JSONB DEFAULT '{}',
    
    -- Statistics
    total_orders INTEGER DEFAULT 0,
    total_spent DECIMAL(10,2) DEFAULT 0.00,
    favorite_items INTEGER[] DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Shopping Carts Table
CREATE TABLE shopping_carts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    facebook_id VARCHAR(255) NOT NULL,
    
    -- Cart Data (stored as JSON for flexibility)
    items JSONB DEFAULT '[]',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key reference
    CONSTRAINT fk_user_profile FOREIGN KEY (facebook_id) REFERENCES user_profiles(facebook_id) ON DELETE CASCADE
);

-- Orders Table
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    facebook_id VARCHAR(255) NOT NULL,
    
    -- Order Details
    items JSONB DEFAULT '[]',
    order_type VARCHAR(20) DEFAULT 'pickup',
    status VARCHAR(20) DEFAULT 'pending',
    
    -- Pricing
    subtotal DECIMAL(10,2) DEFAULT 0.00,
    tax DECIMAL(10,2) DEFAULT 0.00,
    delivery_fee DECIMAL(10,2) DEFAULT 0.00,
    discount DECIMAL(10,2) DEFAULT 0.00,
    total_amount DECIMAL(10,2) DEFAULT 0.00,
    currency VARCHAR(10) DEFAULT 'MMK',
    
    -- Timing
    order_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    pickup_time TIMESTAMP WITH TIME ZONE,
    estimated_ready_time TIMESTAMP WITH TIME ZONE,
    actual_ready_time TIMESTAMP WITH TIME ZONE,
    
    -- Contact Information
    contact_name VARCHAR(255),
    contact_phone VARCHAR(50),
    special_instructions TEXT,
    
    -- Payment
    payment_method VARCHAR(50),
    payment_status VARCHAR(20) DEFAULT 'pending',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key reference
    CONSTRAINT fk_order_user FOREIGN KEY (facebook_id) REFERENCES user_profiles(facebook_id) ON DELETE CASCADE
);

-- Conversation Sessions Table
CREATE TABLE conversation_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    facebook_id VARCHAR(255) NOT NULL,
    
    -- Session State
    current_state VARCHAR(50) DEFAULT 'idle',
    context JSONB DEFAULT '{}',
    
    -- Conversation Data
    messages JSONB DEFAULT '[]',
    intents JSONB DEFAULT '[]',
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    
    -- Statistics
    message_count INTEGER DEFAULT 0,
    user_message_count INTEGER DEFAULT 0,
    bot_message_count INTEGER DEFAULT 0,
    
    -- Foreign key reference
    CONSTRAINT fk_session_user FOREIGN KEY (facebook_id) REFERENCES user_profiles(facebook_id) ON DELETE CASCADE
);

-- User Analytics Table
CREATE TABLE user_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    facebook_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Engagement Metrics
    total_sessions INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    average_session_length DECIMAL(5,2) DEFAULT 0.00,
    last_session_date TIMESTAMP WITH TIME ZONE,
    
    -- Order Metrics
    total_orders INTEGER DEFAULT 0,
    total_spent DECIMAL(10,2) DEFAULT 0.00,
    average_order_value DECIMAL(10,2) DEFAULT 0.00,
    last_order_date TIMESTAMP WITH TIME ZONE,
    
    -- Preference Metrics
    most_ordered_items INTEGER[] DEFAULT '{}',
    favorite_categories VARCHAR(50)[] DEFAULT '{}',
    preferred_order_times VARCHAR(20)[] DEFAULT '{}',
    
    -- Language Preferences
    primary_language VARCHAR(10) DEFAULT 'en',
    language_usage JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key reference
    CONSTRAINT fk_analytics_user FOREIGN KEY (facebook_id) REFERENCES user_profiles(facebook_id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX idx_user_profiles_facebook_id ON user_profiles(facebook_id);
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_orders_facebook_id ON orders(facebook_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_shopping_carts_facebook_id ON shopping_carts(facebook_id);
CREATE INDEX idx_conversation_sessions_facebook_id ON conversation_sessions(facebook_id);
CREATE INDEX idx_user_analytics_facebook_id ON user_analytics(facebook_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_shopping_carts_updated_at BEFORE UPDATE ON shopping_carts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_conversation_sessions_updated_at BEFORE UPDATE ON conversation_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_analytics_updated_at BEFORE UPDATE ON user_analytics FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE shopping_carts ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_analytics ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (basic - you may want to customize these)
CREATE POLICY "Users can view own profile" ON user_profiles FOR SELECT USING (true);
CREATE POLICY "Users can update own profile" ON user_profiles FOR UPDATE USING (true);
CREATE POLICY "Users can insert own profile" ON user_profiles FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can view own cart" ON shopping_carts FOR SELECT USING (true);
CREATE POLICY "Users can update own cart" ON shopping_carts FOR UPDATE USING (true);
CREATE POLICY "Users can insert own cart" ON shopping_carts FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can view own orders" ON orders FOR SELECT USING (true);
CREATE POLICY "Users can update own orders" ON orders FOR UPDATE USING (true);
CREATE POLICY "Users can insert own orders" ON orders FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can view own sessions" ON conversation_sessions FOR SELECT USING (true);
CREATE POLICY "Users can update own sessions" ON conversation_sessions FOR UPDATE USING (true);
CREATE POLICY "Users can insert own sessions" ON conversation_sessions FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can view own analytics" ON user_analytics FOR SELECT USING (true);
CREATE POLICY "Users can update own analytics" ON user_analytics FOR UPDATE USING (true);
CREATE POLICY "Users can insert own analytics" ON user_analytics FOR INSERT WITH CHECK (true); 