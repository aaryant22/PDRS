import matplotlib.pyplot as plt
import pandas as pd

class comparison:
    def __init__(self,count_matrix,file1,file2) -> None:
        self.count_matrix=count_matrix
        self.s1=file1
        self.s2=file2

    def generate_plots(self):
        plt.subplot(1,2,1)
        plt.bar(self.count_matrix.index, self.count_matrix.iloc[:,0], color ='maroon', 
        width = 0.2)
        plt.xlabel("Words")
        plt.ylabel("Count")


        plt.subplot(1,2,2)
        plt.bar(self.count_matrix.index, self.count_matrix.iloc[:,1], color ='purple', 
        width = 0.4)
        plt.xlabel("Words")
        plt.ylabel("Count")

        output_filename = "./static/wordcomparison.png"
        plt.savefig(output_filename, format="png")
        plt.clf()

    def longest_common_string(self):
        m = len(self.s1)
        n = len(self.s2)

        prev = [0] * (n + 1)
        
        res = 0
        end_index_s1 = 0
        
        for i in range(1, m + 1):
        
            curr = [0] * (n + 1)
            for j in range(1, n + 1):
                if self.s1[i - 1] == self.s2[j - 1]:
                    curr[j] = prev[j - 1] + 1
                    if curr[j] > res:
                        res = curr[j]
                        end_index_s1 = i
                else:
                    curr[j] = 0
            
            prev = curr
        
        self.longest_common_substring = self.s1[end_index_s1 - res:end_index_s1]
        