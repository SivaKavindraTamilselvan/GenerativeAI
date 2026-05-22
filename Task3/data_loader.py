# module Document class exists
from langchain_core.documents import Document

# A LangChain object used to store: store the content and metadata
doc=Document(
    # actual knowledge/data.
    page_content="this is the main text content I am using to create RAG",
    # Stores extra information about the document.
    metadata={
        "source":"exmaple.txt",
        "pages":1,
        "author":"Krish Naik",
        "date_created":"2025-01-01"
    }
)
# Create a simple txt file
import os
os.makedirs("data/text_files",exist_ok=True)

# sample texts that contains the page content and metadata
sample_texts = {
    "data/text_files/python_intro.txt": """Python Programming Introduction

Python is a high-level, interpreted programming language known for its simplicity and readability.
Created by Guido van Rossum and first released in 1991, Python has become one of the most popular
programming languages in the world.

Key Features:
- Easy to learn and use
- Extensive standard library
- Cross-platform compatibility
- Strong community support

Python is widely used in web development, data science, artificial intelligence, and automation.""",

    "data/text_files/machine_learning.txt": """Machine Learning Basics

Machine learning is a subset of artificial intelligence that enables systems to learn and improve
from experience without being explicitly programmed. It focuses on developing computer programs
that can access data and use it to learn for themselves.

Types of Machine Learning:
1. Supervised Learning: Learning with labeled data
2. Unsupervised Learning: Finding patterns in unlabeled data
3. Reinforcement Learning: Learning through rewards and penalties

Applications include image recognition, speech processing, and recommendation systems
    """
}

# sample texts item
for filepath, content in sample_texts.items():
    with open(filepath, 'w', encoding="utf-8") as f:
        f.write(content)

print("Sample text files created!")

### TextLoader
from langchain_community.document_loaders import TextLoader

# text loader that loads the data from the documnet
loader=TextLoader("data/text_files/python_intro.txt",encoding="utf-8")
document=loader.load()
print(document)

### Directory Loader
from langchain_community.document_loaders import DirectoryLoader

## load all the text files from the directory
dir_loader=DirectoryLoader(
    "data/text_files",
    glob="**/*.txt", ## Pattern to match files
    loader_cls= TextLoader, ##loader class to use
    loader_kwargs={'encoding': 'utf-8'},
    show_progress=False

)

documents=dir_loader.load()
