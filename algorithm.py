import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns 
import networkx as nx
from matplotlib.patches import Rectangle
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter

class plagiarism_checker:

    def __init__(self,filepath) -> None:
        self.ext = ('.py', '.c', '.cpp', '.txt','.java','.html','.rs')
        self.filepath = filepath
        self.corpus={}
        self.corpus_content=[]
        self.programming_language_files=[]
        self.file_names=[]

    def get_file_content(self):
        for filename in os.listdir(self.filepath):
            if filename.endswith('.docx'):
                file_path = os.path.join(self.filepath, filename)
                self.file_names.append(filename)
                import docx
                doc = docx.Document(file_path)
                text = ''
                for paragraph in doc.paragraphs:
                    text += paragraph.text + '\n'
                self.corpus_content.append(text) 
                self.corpus[filename]=text 
                    
            elif filename.endswith('.pdf'):
                file_path = os.path.join(self.filepath, filename)
                self.file_names.append(filename)
                import PyPDF2
                pdfFileObject = open(file_path, 'rb')
                reader = PyPDF2.PdfReader(pdfFileObject)
                count = len(reader.pages)
                output=""
                for i in range(count):
                    page = reader.pages[i]
                    output += page.extract_text()
                self.corpus_content.append(output)
                self.corpus[filename]=text
            
            elif filename.endswith('.ipynb'):
                file_path = os.path.join(self.filepath, filename)
                self.file_names.append(filename)
                import nbformat
                notebook = nbformat.read(file_path, as_version=4)
                source_code = []
                for cell in notebook.cells:
                    if cell.cell_type == 'code':
                        source_code.append(cell.source)

                notebook_text = '\n'.join(source_code)
                self.corpus_content.append(notebook_text)
                self.corpus[filename]=notebook_text
                
            elif filename.endswith(self.ext):
                file_path = os.path.join(self.filepath, filename)
                try:
                    with open(file_path, encoding='utf-8') as f:
                        self.file_names.append(filename)
                        content = f.read()
                        self.corpus_content.append(content)
                        self.corpus[filename]=content
                        self.programming_language_files.append(content)
                except UnicodeDecodeError:
                    print(f"UnicodeDecodeError: Unable to decode '{filename}'")
    
    def vectorize_content(self):

        cvectorizer = CountVectorizer()
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)

        vectorizer.fit(self.corpus_content)
        cvectorizer.fit(self.corpus_content)

        #sparse matrix and count matrix respectively
        vector = vectorizer.transform(self.corpus_content)
        cvector = cvectorizer.transform(self.corpus_content)

        self.sparse_matrix = pd.DataFrame(vector.toarray(), columns=vectorizer.get_feature_names_out(), index=self.file_names)
        self.count_matrix = pd.DataFrame(cvector.toarray(), columns=cvectorizer.get_feature_names_out(), index=self.file_names)
        unique_words_count = []

        for _, row in self.sparse_matrix.iterrows():
            unique_word_count = sum(1 for value in row.values if value > 0)
            unique_words_count.append(unique_word_count)

    def compute_pairwise_cosine_similarity(self):

        vector_list = self.sparse_matrix.values.tolist()
        self.similarities = []
        n = len(vector_list)
        for i in range(n):
            for j in range(i + 1, n):
                similarity = cosine_similarity([vector_list[i]], [vector_list[j]])[0][0]
                self.similarities.append((i, j, similarity))  #storing indices and similarity score
   
    def compute_similarity_score(self):

        self.pairwise_similarity_score=[]
        for pair in self.similarities:
            index1 = self.sparse_matrix.index[pair[0]]
            index2 = self.sparse_matrix.index[pair[1]]
            similarity_score = round(pair[2] * 100, 2)
            self.pairwise_similarity_score.append([index1,index2,similarity_score])

        scores = [sublist[2] for sublist in self.pairwise_similarity_score]
        self.highest_plagiarism_score = max(scores)

    def detect_top_programming_lang(self):
        keywords_folder = r'./keywords' #add path
        keyword_contents = {}
        for filename in os.listdir(keywords_folder):
            if filename.endswith('.txt'):
                file_path = os.path.join(keywords_folder, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                    lines = [line.strip() for line in lines]
                    file_name = os.path.splitext(filename)[0]
                    keyword_contents[file_name] = lines

        languages_detected = []
        for file_contents in self.programming_language_files:
            max_keywords = 0
            max_language = None
            for language, keywords in keyword_contents.items():
                keywords_found = sum(1 for keyword in keywords if keyword in file_contents)
                if keywords_found > max_keywords:
                    max_keywords = keywords_found
                    max_language = language
            if max_language:
                languages_detected.append(max_language)

        self.toplang = Counter(languages_detected).most_common(1)[0][0]
    
    def compute_similarity_matrix(self):
        n = len(self.sparse_matrix)
        self.similarity_matrix = np.zeros((n, n))
        for pair in self.similarities:
            i, j, similarity_score = pair
            self.similarity_matrix[i, j] = similarity_score
            self.similarity_matrix[j, i] = similarity_score
            
    def plot_top_50_words(self):
        
        frequency_df = pd.DataFrame(self.count_matrix.sum(), columns=['Frequency'])
        frequency_df = frequency_df.sort_values(by='Frequency', ascending=False)

        top = frequency_df.head(50)
        top.plot(kind='bar')
        plt.title('Top 50 Words by Frequency')
        plt.xlabel('Word')
        plt.ylabel('Frequency')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        output_filename = "./static/top50words.png"
        plt.savefig(output_filename, format="png")
        plt.clf()

    def generate_network_plot(self):
        G = nx.Graph()

        for i in range(len(self.similarity_matrix)):
            G.add_node(i)

        for i in range(len(self.similarity_matrix)):
            for j in range(i + 1, len(self.similarity_matrix[i])):
                similarity = self.similarity_matrix[i][j]
                if similarity > 0.1:
                    G.add_edge(i, j, weight=similarity, label=f'{1 - similarity:.2f}')
                    
        n = len(self.sparse_matrix)
        pos = nx.spring_layout(G, center=[0.5,0.5],k=0.3,scale=15)
        nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=250, font_size=6, font_color='black',
                edge_color='gray', width=2)
        edge_labels = nx.get_edge_attributes(G, 'label')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=4,font_color='black')
        # Create a border around the plot
        border = Rectangle((plt.xlim()[0], plt.ylim()[0]), plt.xlim()[1] - plt.xlim()[0], plt.ylim()[1] - plt.ylim()[0],
                        edgecolor='black', linewidth=2, facecolor='none')
        plt.gca().add_patch(border)
            #plt.axis('on')  # Show axes
        plt.title('Graph of Cosine Similarity')
        output_filename = "./static/clustermap.png"
        plt.savefig(output_filename, format="png")
        plt.clf()

    def generate_heatmap(self):
        hdf=self.sparse_matrix
        hdf.index = np.arange(1,len(hdf)+1)
        hindex=hdf.index
        n = len(self.sparse_matrix)
        self.similarity_matrix = np.zeros((n, n))
        for pair in self.similarities:
            i, j, similarity_score = pair
            self.similarity_matrix[i, j] = similarity_score
            self.similarity_matrix[j, i] = similarity_score
        print(hdf.head())
        #check colormaps once
        plt.figure(figsize=(10,8))
        sns.heatmap(self.similarity_matrix, annot=True, fmt=".2f", xticklabels=hindex, yticklabels=hindex, cmap="YlGnBu")
        plt.title("Similarity Matrix")
        plt.xlabel("Files")
        plt.ylabel("Files")
        plt.xticks(rotation=90)
        plt.yticks(rotation=0)
        plt.tight_layout()
        output_filename = "./static/similarityheatmap.png"
        plt.savefig(output_filename, format="png")
        plt.clf()

    # return self.pairwise_similarity_score, self.corpus_content, plaghighest, toplang

if __name__ == '__main__':
    obj = plagiarism_checker(r"") #Enter your filepath here
    obj.get_file_content()
    obj.vectorize_content()
    obj.compute_pairwise_cosine_similarity()
    obj.compute_similarity_score()
    obj.detect_top_programming_lang()
    obj.compute_similarity_matrix()
    obj.plot_top_50_words()
    obj.generate_network_plot()
    obj.generate_heatmap()