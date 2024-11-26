import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px


def main():
    st.set_page_config(
        page_title="Demografia Kanady",
        page_icon="🇨🇦",
        layout="wide"
    )

    st.markdown("# Demografia Kanady")
    st.markdown("## *Populacja*")

    df = pd.read_pickle("data/interim/population.csv")
    df_avg = pd.read_pickle("data/interim/population_averages.csv")
    df_ur_zg = pd.read_pickle("data/interim/deaths_births.csv")
    df_zg = pd.read_pickle("data/interim/causes_of_death.csv")

    filtr_obszar = st.selectbox(label="Obszar", 
                                        placeholder="Wybierz Obszar", 
                                        options=df["Obszar"].unique())
    filtry_plec = st.multiselect(label="Płeć", placeholder="Wybierz Płeć",
                options=["Wszyscy", "Kobiety", "Mężczyźni"],
                default="Wszyscy")

    st.markdown("---")

    def prepare_plot_data(df, selected_plec_filters, selected_wiek_filters, obszar):
        filt = (df["Plec"].isin(selected_plec_filters)) & (df["Obszar"].isin(obszar)) & (df["Wiek"].isin(selected_wiek_filters))
        return df[filt]



    col1, col2 = st.columns(2)

    with col1:
        if filtr_obszar != "Canada":
            title = f"Liczba ludności {filtr_obszar} w latach 1971-2024"
        else:
            title = "Liczba ludności Kanady w latach 1971-2024"
        
        filtry_wiek = st.multiselect(label="Wiek", 
                                placeholder="Wybierz Przedział Wiekowy",
                                options=df["Wiek"].unique(),
                                default="Wszyscy")
        df_plot = prepare_plot_data(df, filtry_plec, filtry_wiek, [filtr_obszar])
        df_plot['Wiek_Plec'] = df_plot['Wiek'].astype("str") + " - " + df_plot['Plec'].astype("str")
        fig = px.line(df_plot, x="Rok", y="Wartosc", color="Wiek_Plec", line_group="Plec",
                    labels={"Plec":"Płeć"}, 
                    title=title)
        fig.update_layout(dragmode="pan",
                    width=1200,
                    height=500,
                    yaxis_title="Liczba ludności",
                    legend=dict(font=dict(size=16)))
        fig.update_traces(line={'width': 7})
        st.plotly_chart(fig, config={"scrollZoom": True})

    with col2:
        filtry_miary = st.multiselect("Miara położenia", 
                    options=["Średnia", "Mediana"],
                    default="Średnia")
        
        if (len(filtry_miary) > 1) & (filtr_obszar == "Canada"):
            title = f"Mediana i Średnia wieku w Kanadzie w latach 1971-2024"
        elif (len(filtry_miary) > 1) & (filtr_obszar != "Canada"):
            title = f"Mediana i Średnia wieku w {filtr_obszar} w latach 1971-2024"
        elif (len(filtry_miary) < 2) & (filtr_obszar == "Canada"):
            title = f"{filtry_miary[0]} wieku w Kanadzie w latach 1971-2024"
        else:
            title = f"Mediana i Średnia wieku {filtr_obszar} w latach 1971-2024"

        df_plot_avg = prepare_plot_data(df=df_avg,
                                    selected_plec_filters=filtry_plec, 
                                    selected_wiek_filters=filtry_miary,
                                    obszar=[filtr_obszar])

        df_plot_avg['Miara_Plec'] = df_plot_avg['Wiek'].astype("str") + " - " + df_plot_avg['Plec'].astype("str")



        fig = px.line(df_plot_avg, x="Rok", y="Wartosc", color="Miara_Plec", line_group="Plec",
                        labels={"Plec":"Płeć"}, 
                        title=title)
        fig.update_layout(dragmode="pan",
                        width=1200,
                        height=500,
                        yaxis_title="Wiek",
                        legend=dict(font=dict(size=16)))   
        fig.update_traces(line={'width': 7})
        st.plotly_chart(fig, config={"scrollZoom": True})

    st.markdown("---")
    filtr_rok = st.selectbox(label="Rok", placeholder="Wybierz rok",
                            options=df["Rok"].unique())

    def prepare_map(df):
        geojson = gpd.read_file("data/raw/canada_provinces.geo.json")
        geojson.rename(columns={"name": "Obszar"}, inplace=True)

        df = prepare_plot_data(df, ["Wszyscy"], ["Wszyscy"], df["Obszar"].unique()[0:12])
        filt = df["Rok"] == filtr_rok
        df_filt = df[filt]
        df_filt["Wartosc"] = df_filt["Wartosc"].astype('int64')

        filt = df_filt["Obszar"] == "Canada"
        liczba_ludnosci_ogolem = df_filt[filt]["Wartosc"][0]
        
        filt = df_filt["Wartosc"] == df_filt[~filt]["Wartosc"].max()
        max_prowincja = df_filt[filt][["Obszar", "Wartosc"]]
        
        filt = df_filt["Wartosc"] == df_filt[~filt]["Wartosc"].min()
        min_prowincja = df_filt[filt][["Obszar", "Wartosc"]]    
        
        
        geo_df = gpd.GeoDataFrame.from_features(geojson).merge(df_filt, on="Obszar").set_index("Obszar")
        return geo_df, liczba_ludnosci_ogolem, max_prowincja, min_prowincja

    geo_df, liczba_ludnosci_ogolem, max_prowincja, min_prowincja = prepare_map(df)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.choropleth(
            geo_df,
            geojson=geo_df.geometry,
            locations=geo_df.index,
            color="Wartosc",
            projection="mercator",
            color_continuous_scale="Viridis"
        )

        fig.update_geos(
            fitbounds="locations", 
            visible=False,
            projection_scale=5,
            center={"lat": 60, "lon": -95}
        )
        fig.update_layout(
            width=1200,  
            height=600, 
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            legend=dict(font=dict(size=16))
        )

        st.markdown(f"### Liczba ludności w prowincjach Kanady w {int(geo_df["Rok"].unique())}:")
        st.write(f"* **{liczba_ludnosci_ogolem}** mieszkańców w całej Kanadzie")
        st.write(f"* **{max_prowincja.iloc[0,0]}** najbardziej liczną prowincją ({max_prowincja.iloc[0,1]} mieszkańców)")
        st.write(f"* **{min_prowincja.iloc[0,0]}** najmniej liczną prowincją ({min_prowincja.iloc[0,1]} mieszkańców)")

        st.plotly_chart(fig, use_container_width=False)

    def prepare_barchart(df):
        df = prepare_plot_data(df=df, 
                            selected_plec_filters=["Kobiety", "Mężczyźni"],
                            selected_wiek_filters=df["Wiek"].unique(),
                            obszar=["Canada"])
        filt = (df["Wiek"] != "Wszyscy") & (df["Rok"] == filtr_rok)
        df = df[filt]
        
        df['Wiek'] = df['Wiek'].astype("str")
        najliczniejszy_przedzial = df.groupby(by="Wiek")["Wartosc"].sum().idxmax()
        
        df_sredni_wiek = prepare_plot_data(df=df_avg, 
                                        selected_plec_filters=["Kobiety", "Mężczyźni"],
                                        obszar=["Canada"],
                                        selected_wiek_filters=["Średnia"])
        filt = df_sredni_wiek["Rok"] == filtr_rok    
        df_sredni_wiek=df_sredni_wiek[filt]
        
        sredni_wiek_m = df_sredni_wiek[df_sredni_wiek["Plec"] == "Mężczyźni"]["Wartosc"].iloc[0]
        sredni_wiek_k = df_sredni_wiek[df_sredni_wiek["Plec"] == "Kobiety"]["Wartosc"].iloc[0]
        
        return df, najliczniejszy_przedzial, sredni_wiek_m, sredni_wiek_k

    barplot_df, najliczniejszy_przedzial, sredni_wiek_m, sredni_wiek_k = prepare_barchart(df=df)

    with col2:
        st.markdown(f"### Struktura wieku ludności Kanady w {filtr_rok}:")
        st.write(f"* Najwięcej osób należało do przedziału **{najliczniejszy_przedzial}**")    
        st.write(f"* Średnia wieku kobiet: **{sredni_wiek_k}**")
        st.write(f"* Średnia wieku mężczyzn: **{sredni_wiek_m}**")
            
        fig = px.bar(
            data_frame=barplot_df, 
            x="Wiek", 
            color="Plec",
            y='Wartosc',
            barmode="group",
            color_discrete_map={
                "Mężczyźni": "#00b9ff",
                "Kobiety": "#ff4600"
            }
        )
        fig.update_layout(
            width=1200,  
            height=550, 
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            legend=dict(font=dict(size=16)),
            xaxis=dict(
                tickfont=dict(size=16) 
            ),
            yaxis=dict(
                tickfont=dict(size=16)
            )
        )
        st.plotly_chart(fig)

    st.markdown("---")
    st.markdown("## *Urodzenia i Zgony*")

    df_ur_zg = df_ur_zg.melt(id_vars="Rok", var_name="Category", value_name="Wartosc")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.line(
            data_frame=df_ur_zg, 
            x="Rok", 
            y="Wartosc", 
            color="Category",
            color_discrete_map={"Urodzenia": "green", "Zgony": "red"},
            title="Liczba urodzeń i zgonów w Kanadzie w latach 1991-2022"
        )
        fig.update_traces(line={'width': 7})
        fig.update_layout(
            legend=dict(font=dict(size=18)), 
            height=800,
            xaxis=dict(
                tickfont=dict(size=18),  
                title=dict(
                    text="Rok",          
                    font=dict(size=18)   
                )
            ),
            yaxis=dict(
                tickfont=dict(size=18),  
                title=dict(
                    text="Wartosc",      
                    font=dict(size=18)  
                )
            )
        )

        st.plotly_chart(fig)



    def prepare_causes_of_death_plot(df, rok, plec, wiek):
        filt = (
            (df["Rok"] == rok) &
            (df["Plec"] == plec) &
            (df["Wiek_w_dniu_smierci"] == wiek) &
            (df["Przyczyna_smierci"] != 'Total, all causes of death')
        )
        df = df[filt]
        
        df["Przyczyna_smierci"] = df["Przyczyna_smierci"].apply(
            lambda x: x[:30] + "..." if len(x) > 30 else x
        )
        
        df = df.sort_values(by="Ilosc_zgonow", ascending=False).iloc[0:15, :] 
        
        return df

    # df_zg_plot= prepare_causes_of_death_plot(df=df_zg, rok=2010, plec="Kobiety", wiek="Wszyscy")

    # fig = px.bar(df_zg_plot, 
    #              orientation="h", 
    #              y="Przyczyna_smierci", 
    #              x="Ilosc_zgonow",
    #              color="Plec",
    #              barmode="group")

    with col2:
        filtr_rok = st.selectbox("Rok", options=df_zg["Rok"].unique())
        filtr_plec = st.selectbox("Plec", options=df_zg["Plec"].unique())
        filtr_wiek = st.selectbox("Wiek w dniu zgonu", options=df_zg["Wiek_w_dniu_smierci"].unique())

        df_zg_plot= prepare_causes_of_death_plot(df=df_zg, 
                                                    rok=filtr_rok, 
                                                    plec=filtr_plec, 
                                                    wiek=filtr_wiek)

        fig = px.bar(df_zg_plot, 
                    orientation="h", 
                    y="Przyczyna_smierci", 
                    x="Ilosc_zgonow",
                    title=f"""Najczęstsze przyczyny zgonów mieszkańców Kanady w {filtr_rok} (Płeć: {filtr_plec}, Wiek: {filtr_wiek})""")
        fig.update_layout(
            yaxis=dict(
                title=dict(font=dict(size=18), text="Przyczyna śmierci"), 
                tickfont=dict(size=18)       
            ),
            xaxis=dict(
                title=dict(font=dict(size=18), text="Ilość zgonów"), 
                tickfont=dict(size=18)),     
            height=560
        )    
        st.plotly_chart(fig)
        
try:
    main()
except Exception as e:
    st.error("Wystąpił nieoczekiwany błąd. Odśwież stronę, aby spróbować ponownie.")