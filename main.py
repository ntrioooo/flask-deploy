from flask import Flask, render_template, request
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
import os

app = Flask(__name__)

def perform_clustering():
    # Load dataset
    df = pd.read_excel("./data/data_makanan_terbaru.xls")

    # Selection data
    df = df.drop(columns=['id', 'karbohidrat', 'lemak'])

    # Transformation data
    scaler = MinMaxScaler()
    df[['kalori', 'protein']] = scaler.fit_transform(df[['kalori', 'protein']])

    

    # Clustering with K-means
    kmeans = KMeans(n_clusters=2, random_state=2)
    df['cluster'] = kmeans.fit_predict(df[['kalori', 'protein']])

    print(df)
    return df

def harris_benedict(jenis_kelamin, umur, berat_badan, tinggi_badan, faktor_aktivitas):
    if jenis_kelamin == "l":
        bmr = 66 + (13.7 * berat_badan) + (5 * tinggi_badan) - (6.8 * umur)
        faktor_aktivitas_laki = {
            "sangat_ringan": 1.3,
            "ringan": 1.56,
            "sedang": 1.76,
            "berat": 2.1
        }
        faktor_aktivitas = faktor_aktivitas_laki[faktor_aktivitas]
    elif jenis_kelamin == "p":
        bmr = 655 + (9.6 * berat_badan) + (1.8 * tinggi_badan) - (4.7 * umur)
        faktor_aktivitas_perempuan = {
            "sangat_ringan": 1.3,
            "ringan": 1.55,
            "sedang": 1.7,
            "berat": 2.0
        }
        faktor_aktivitas = faktor_aktivitas_perempuan[faktor_aktivitas]
    return bmr * faktor_aktivitas

def adjust_calories(selected_foods, calorie_requirement):
    total_calories = sum(food[1] for food in selected_foods)
    if calorie_requirement > 2000 and calorie_requirement <= 2500:
        for i in range(len(selected_foods)):
            food = selected_foods[i]
            adjusted_calories = food[1] * 1.25
            selected_foods[i] = (food[0], adjusted_calories, food[2])
        # Recalculate total calories
        total_calories = sum(food[1] for food in selected_foods)
    elif calorie_requirement > 2500 and calorie_requirement <= 3000:
        for i in range(len(selected_foods)):
            food = selected_foods[i]
            adjusted_calories = food[1] * 1.7
            selected_foods[i] = (food[0], adjusted_calories, food[2])
        # Recalculate total calories
        total_calories = sum(food[1] for food in selected_foods)
    elif calorie_requirement > 3000:
        for i in range(len(selected_foods)):
            food = selected_foods[i]
            adjusted_calories = food[1] * 2.1
            selected_foods[i] = (food[0], adjusted_calories, food[2])
        # Recalculate total calories
        total_calories = sum(food[1] for food in selected_foods)
    return selected_foods, total_calories

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Process form data
        jenis_kelamin = request.form['jenis_kelamin']
        umur = int(request.form['umur'])
        berat_badan = float(request.form['berat_badan'])
        tinggi_badan = float(request.form['tinggi_badan'])
        nama = request.form['nama']
        faktor_aktivitas = request.form['kategori_aktivitas']

        # Calculate BMR
        kebutuhan_kalori = harris_benedict(jenis_kelamin, umur, berat_badan, tinggi_badan, faktor_aktivitas)

        # Perform clustering
        df = perform_clustering()

        # Find menu for breakfast and lunch
        menu_pagi = df[df['cluster'] == 1]
        menu_siang = df[df['cluster'] == 0]

        # Select one food from each category for breakfast
        selected_foods_pagi = []
        categories = ['makanan pokok', 'lauk', 'sayuran', 'buah']
        for category in categories:
            food = menu_pagi[menu_pagi['jenis_makanan'] == category]
            if not food.empty:
                food_sample = food.sample(1)
                selected_foods_pagi.append((food_sample['Nama makanan'].values[0], food_sample['kalori'].values[0], food_sample['jenis_makanan'].values[0]))
            else:
                selected_foods_pagi.append((f"Tidak ada makanan {category} di menu pagi", 0, category))

        # Select one food from each category for lunch
        selected_foods_siang = []
        for category in categories:
            food = menu_siang[menu_siang['jenis_makanan'] == category]
            if not food.empty:
                food_sample = food.sample(1)
                selected_foods_siang.append((food_sample['Nama makanan'].values[0], food_sample['kalori'].values[0], food_sample['jenis_makanan'].values[0]))
            else:
                selected_foods_siang.append((f"Tidak ada makanan {category} di menu siang", 0, category))

        # Calculate total calories for breakfast and lunch
        total_calories_pagi = sum(food[1] for food in selected_foods_pagi)
        total_calories_siang = sum(food[1] for food in selected_foods_siang)

        # Adjust total calories if they exceed daily calorie requirement
        selected_foods_pagi, total_calories_pagi = adjust_calories(selected_foods_pagi, kebutuhan_kalori)
        selected_foods_siang, total_calories_siang = adjust_calories(selected_foods_siang, kebutuhan_kalori)

        if total_calories_pagi + total_calories_siang > kebutuhan_kalori:
            # Adjust total calories for breakfast and lunch if they exceed daily calorie requirement
            ratio = kebutuhan_kalori / (total_calories_pagi + total_calories_siang)
            total_calories_pagi *= ratio
            total_calories_siang *= ratio

        # Render template with results
        if total_calories_pagi + total_calories_siang > kebutuhan_kalori:
            error_message = "Total kalori makanan pagi dan siang melebihi kebutuhan kalori harian."
            return render_template("result.html", error_message=error_message, kebutuhan_kalori="{:.2f}".format(kebutuhan_kalori),
                            selected_foods_pagi=selected_foods_pagi, total_calories_pagi="{:.2f}".format(total_calories_pagi),
                            selected_foods_siang=selected_foods_siang, total_calories_siang="{:.2f}".format(total_calories_siang), 
                            nama=nama)
        else:
            return render_template("result.html", kebutuhan_kalori="{:.2f}".format(kebutuhan_kalori),
                            selected_foods_pagi=selected_foods_pagi, total_calories_pagi="{:.2f}".format(total_calories_pagi),
                            selected_foods_siang=selected_foods_siang, total_calories_siang="{:.2f}".format(total_calories_siang), 
                            nama=nama)
    else:
        # Render form template
        return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))