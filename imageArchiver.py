import requests
import io
from supabase import create_client, Client
from PIL import Image
import os
from dotenv import load_dotenv
load_dotenv()

# Initialize Supabase client 
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


def download_image(url):
    response = requests.get(url)
    return Image.open(io.BytesIO(response.content))

def save_image_to_supabase(image, file_name, bucket_name):
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    # Upload to Supabase Storage
    # bucket_name = "social_bucket"
    file_path = f"cover_images/{file_name}"
    supabase.storage.from_(bucket_name).upload(file_path, img_byte_arr)
    
    # Get public URL
    public_url = supabase.storage.from_(bucket_name).get_public_url(file_path)
    
    return public_url

def process_single_link(image_link, file_name, bucket_name):
    if image_link:
        try:
            image = download_image(image_link)
            # file_name = image_link.split('/')[-1]  # Extract file name from URL
            
            public_url = save_image_to_supabase(image, file_name, bucket_name)
            #print(f"Saved image: {file_name}, Public URL: {public_url}")
            return public_url
        except Exception as e:
            print(f"Error processing image {image_link}: {str(e)}")
            return None

# Usage
def uploadImageExample():
    image_link = 'https://instagram.fiev22-1.fna.fbcdn.net/v/t51.29350-15/431180174_401607359233445_4256402937220781300_n.jpg?stp=dst-jpg_e15&efg=eyJ2ZW5jb2RlX3RhZyI6ImltYWdlX3VybGdlbi4xMDgweDE5MjAuc2RyLmYyOTM1MCJ9&_nc_ht=instagram.fiev22-1.fna.fbcdn.net&_nc_cat=105&_nc_ohc=pGD0o64JYfUQ7kNvgGDXQh5&edm=ABmJApABAAAA&ccb=7-5&ig_cache_key=MzMxNDE3MTM2NTM4ODE1MTI4MQ%3D%3D.2-ccb7-5&oh=00_AYDK9BkugAUiX9_E4Bvc8qAtsTehgoJUtTJ5n0VyPoabpA&oe=6693533C&_nc_sid=b41fef'
    file_name = 'IG_garyvee_00'
    bucket_name='social_bucket'
    result = process_single_link(image_link, file_name, bucket_name)
    if result:
        print(f"Image successfully saved. Public URL: {result}")
    else:
        print("Failed to save the image.")

# Usage
def uploadImage(image_link, file_name, bucket_name):
    result = process_single_link(image_link, file_name, bucket_name)
    if result:

        # save link to cached image in supabase table
        print(f"Image successfully saved. Public URL: {result}")
        response = (supabase.table("instagram").upsert({"post_code": file_name, "saved_cover_image": result}, on_conflict="post_code",).execute())
       # response = (supabase.table("users").upsert({"id": 42, "handle": "saoirse", "display_name": "Saoirse"},on_conflict="handle",) .execute())


    else:
        print(f"Failed to save the image: {file_name}")


if 1 == 2:
    uploadImage()

access_key_id = '7b69b86cd523c99444877540d97c29a2'
secret_access_key = '0d464d697f6a328c959be68df5c51aba8fbca0a2b4cd0f0c21b0dc38cc52657f'