from googletrans import Translator

# Create an array of words
my_array = ["你好", "Hi", "Hola Mundo"]

# Initialize the translator
translator = Translator()

# Translate each word in the array
translated_array = [translator.translate(word, dest="en").text for word in my_array]

# Print the translated array
print(translated_array)