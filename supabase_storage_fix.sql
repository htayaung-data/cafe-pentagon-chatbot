-- Supabase Storage Bucket Policy Fix for Facebook Messenger
-- Run these commands in your Supabase SQL editor

-- 1. Create a new bucket specifically for Facebook-compatible images
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'cafepentagon-public',
    'cafepentagon-public',
    true,
    52428800, -- 50MB limit
    ARRAY['image/jpeg', 'image/png', 'image/gif', 'image/webp']
)
ON CONFLICT (id) DO NOTHING;

-- 2. Create policy for public read access to images
CREATE POLICY "Public read access for images" ON storage.objects
FOR SELECT USING (
    bucket_id = 'cafepentagon-public' 
    AND (storage.foldername(name))[1] = 'images'
);

-- 3. Create policy for authenticated uploads
CREATE POLICY "Authenticated uploads for images" ON storage.objects
FOR INSERT WITH CHECK (
    bucket_id = 'cafepentagon-public'
    AND auth.role() = 'authenticated'
);

-- 4. Create policy for authenticated updates
CREATE POLICY "Authenticated updates for images" ON storage.objects
FOR UPDATE USING (
    bucket_id = 'cafepentagon-public'
    AND auth.role() = 'authenticated'
);

-- 5. Create policy for authenticated deletes
CREATE POLICY "Authenticated deletes for images" ON storage.objects
FOR DELETE USING (
    bucket_id = 'cafepentagon-public'
    AND auth.role() = 'authenticated'
);

-- 6. Enable CORS for Facebook domains
-- Note: This needs to be done in Supabase Dashboard > Storage > Settings

-- 7. Create a function to generate Facebook-compatible URLs
CREATE OR REPLACE FUNCTION get_facebook_image_url(image_path TEXT)
RETURNS TEXT AS $$
BEGIN
    -- Return the public URL for the image
    RETURN 'https://' || current_setting('app.settings.supabase_url') || '/storage/v1/object/public/cafepentagon-public/' || image_path;
END;
$$ LANGUAGE plpgsql;

-- 8. Create a view for menu items with Facebook-compatible URLs
CREATE OR REPLACE VIEW menu_items_with_facebook_urls AS
SELECT 
    id,
    category,
    english_name,
    myanmar_name,
    price,
    currency,
    CASE 
        WHEN image_url IS NOT NULL THEN 
            'https://' || current_setting('app.settings.supabase_url') || '/storage/v1/object/public/cafepentagon-public/' || 
            REPLACE(image_url, 'https://qniujcgwyphkfnnqhjcq.supabase.co/storage/v1/object/public/cafepentagon//', '')
        ELSE image_url
    END as facebook_image_url,
    ingredients,
    dietary_info,
    allergens,
    description_en,
    description_mm,
    spice_level,
    preparation_time
FROM menu_items;

-- 9. Update existing image URLs to use the new bucket structure
-- This will help with Facebook compatibility
UPDATE menu_items 
SET image_url = REPLACE(
    image_url, 
    'https://qniujcgwyphkfnnqhjcq.supabase.co/storage/v1/object/public/cafepentagon//',
    'https://qniujcgwyphkfnnqhjcq.supabase.co/storage/v1/object/public/cafepentagon-public/'
)
WHERE image_url LIKE '%supabase.co/storage/v1/object/public/cafepentagon//%';

-- 10. Create a function to validate Facebook image URLs
CREATE OR REPLACE FUNCTION is_facebook_compatible_url(url TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    -- Check if URL is from a Facebook-trusted domain
    RETURN url LIKE '%supabase.co%' 
        OR url LIKE '%imgur.com%' 
        OR url LIKE '%cloudinary.com%'
        OR url LIKE '%amazonaws.com%'
        OR url LIKE '%cloudfront.net%';
END;
$$ LANGUAGE plpgsql;