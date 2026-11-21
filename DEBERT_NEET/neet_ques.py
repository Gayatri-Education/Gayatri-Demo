import pandas as pd
import matplotlib.pyplot as plt
data_files=["C:\\projects\\neet pyqs\\dbert\\neet_pyqs_csv\\aiims_2013_questions.csv",
            "C:\\projects\\neet pyqs\\dbert\\neet_pyqs_csv\\AIPMT_2014_Questions.csv",
            "C:\\projects\\neet pyqs\\dbert\\neet_pyqs_csv\\NEET_AIPMT_2015_Code_A_dataset_final.csv",
            "C:\\projects\\neet pyqs\\dbert\\neet_pyqs_csv\\NEET_2016_Phase_1_Code_APW_dataset.csv",
            "C:\\projects\\neet pyqs\\dbert\\neet_pyqs_csv\\NEET_2017_Code_A_dataset.csv",
            "C:\\projects\\neet pyqs\\dbert\\neet_pyqs_csv\\NEET_2018_Code_AA_dataset.csv",
            "C:\\projects\\neet pyqs\\dbert\\neet_pyqs_csv\\NEET_2019_Code_P1_dataset.csv",
            "C:\\projects\\neet pyqs\\dbert\\neet_pyqs_csv\\NEET_2020_Code_E1_dataset.csv",
            "C:\\projects\\neet pyqs\\dbert\\neet_pyqs_csv\\NEET_2021_Code_M1_dataset.csv",
            "C:\\projects\\neet pyqs\\dbert\\neet_pyqs_csv\\neet_2022_q1_dataset_biology.csv",
            "C:\\projects\\neet pyqs\\dbert\\neet_pyqs_csv\\neet_2023_e1_dataset_biology.csv",
            "C:\\projects\\neet pyqs\\dbert\\neet_pyqs_csv\\neet_2024_dataset_final_biology.csv",
            "C:\\projects\\neet pyqs\\dbert\\neet_pyqs_csv\\neet_2025_dataset_final_biology.csv",
            "C:\\projects\\neet pyqs\\dbert\\neet_pyqs_csv\\neet_2026_re_neet_code60_dataset_final.csv",
            ]
for i in data_files:
    data = pd.read_csv(i)
    if (data["year"]==2013).any():
        data.drop(data[data['subject']=='General Knowledge'].index, inplace=True)
    for j in data["subject"].unique():
        sub=data[(data['subject'] == j)]['chapter']
        sub_questions=(sub.value_counts())/(sub.value_counts().sum())
        print(sub_questions*100)
        print(data.columns)
        plt.figure(figsize=(12, 8))
        plt.bar(sub_questions.index, sub_questions.values,color='lightgreen')
        plt.title(f'{j} Questions Distribution {data.year.unique()[0]}')
        plt.xlabel('Chapter')
        plt.ylabel('Proportion')
        plt.xticks(rotation=90)
        plt.tight_layout()
        plt.show()
    
 