from flask import Flask, render_template, request
import pandas as pd
from sklearn.cluster import KMeans
import os

app = Flask(__name__)

def perform_clustering():
    # Load dataset
    df = pd.read_csv("./data/makanan_updated_csv.csv")

    # print("Data sebelum preprocessing:")
    # print(df.head())

    # Clustering with K-means
    kmeans = KMeans(n_clusters=2, random_state=2)
    df['cluster'] = kmeans.fit_predict(df[['kalori', 'protein']])

    # print("\nData setelah clustering:")
    # print(df.head())

    return df

# Calculate Harris-Benedict BMR
def harris_benedict(jenis_kelamin, umur, berat_badan, tinggi_badan, faktor_aktivitas):
    if jenis_kelamin == "l":
        bmr = 66 + (13.75 * berat_badan) + (5 * tinggi_badan) - (6.8 * umur)
    elif jenis_kelamin == "p":
        bmr = 655 + (9.6 * berat_badan) + (1.8 * tinggi_badan) - (4.7 * umur)
    return bmr * faktor_aktivitas

kategori_aktivitas_dict = {
    "sangat_ringan": 1.30,
    "ringan": 1.65,
    "sedang": 1.76,
    "berat": 2.10
}   

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Process form data
        jenis_kelamin = request.form['jenis_kelamin']
        umur = int(request.form['umur'])
        berat_badan = float(request.form['berat_badan'])
        tinggi_badan = float(request.form['tinggi_badan'])
        nama = request.form['nama']
        faktor_aktivitas = kategori_aktivitas_dict[request.form['kategori_aktivitas']]

        # Calculate BMR
        kebutuhan_kalori = harris_benedict(jenis_kelamin, umur, berat_badan, tinggi_badan, faktor_aktivitas)

        # Perform clustering
        df = perform_clustering()

        # Find menu for breakfast and lunch
        menu_pagi = df[df['cluster'] == 0]
        menu_siang = df[df['cluster'] == 1]

        # Select one food from each category for breakfast
        selected_foods_pagi = []
        categories = ['pokok', 'lauk', 'sayur', 'buah']
        for category in categories:
            food = menu_pagi[menu_pagi['jenis'] == category].sample(1)
            selected_foods_pagi.append((food['nama_makanan'].values[0], food['kalori'].values[0], food['jenis'].values[0]))

        # Select one food from each category for lunch
        selected_foods_siang = []
        for category in categories:
            food = menu_siang[menu_siang['jenis'] == category].sample(1)
            selected_foods_siang.append((food['nama_makanan'].values[0], food['kalori'].values[0], food['jenis'].values[0]))

        # Calculate total calories for breakfast and lunch
        total_calories_pagi = sum(food[1] for food in selected_foods_pagi)
        total_calories_siang = sum(food[1] for food in selected_foods_siang)


        # Render template with results
        return render_template("result.html", kebutuhan_kalori=kebutuhan_kalori,
                               selected_foods_pagi=selected_foods_pagi, total_calories_pagi=total_calories_pagi,
                               selected_foods_siang=selected_foods_siang, total_calories_siang=total_calories_siang, 
                               nama=nama)
    else:
        # Render form template
        return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))