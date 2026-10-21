import streamlit as st
import pandas as pd
import plotly.express as px

# =====================================================
# CONFIGURAÇÃO
# =====================================================

st.set_page_config(
    page_title="Dashboard SPI Motorola",
    layout="wide"
)

st.title("📊 Dashboard SPI Motorola")

# =====================================================
# UPLOAD
# =====================================================

arquivo = st.file_uploader(
    "Selecione o Excel SPI",
    type=["xlsx"]
)

if arquivo:

    try:

        excel = pd.ExcelFile(arquivo)

        # =====================================================
        # LOCALIZAÇÃO DAS ABAS
        # =====================================================

        abas_volume = [
            aba for aba in excel.sheet_names
            if "volume" in aba.lower()
        ]

        abas_premium = [
            aba for aba in excel.sheet_names
            if "premium" in aba.lower()
        ]

        aba_promotores = next(
            aba for aba in excel.sheet_names
            if "promotores" in aba.lower()
        )

        aba_hunters = next(
            aba for aba in excel.sheet_names
            if "hunters" in aba.lower()
        )

        # =====================================================
        # SIDEBAR
        # =====================================================

        semana = st.sidebar.selectbox(
            "Semana",
            sorted(abas_volume, reverse=True)
        )

        periodo = st.sidebar.selectbox(
            "Período",
            [
                "Week -1",
                "Week -2",
                "Week -3",
                "Week -4",
                "Week -5",
                "Week -6"
            ]
        )

        semana_num = semana.lower().split("w")[-1].strip()

        premium_aba = next(
            aba
            for aba in abas_premium
            if aba.lower().endswith(
                "w" + semana_num
            )
        )

        # =====================================================
        # LEITURA
        # =====================================================

        volume = pd.read_excel(
            arquivo,
            sheet_name=semana
        )

        premium = pd.read_excel(
            arquivo,
            sheet_name=premium_aba
        )

        promotores = pd.read_excel(
            arquivo,
            sheet_name=aba_promotores
        )

        hunters = pd.read_excel(
            arquivo,
            sheet_name=aba_hunters
        )

        # =====================================================
        # BASE
        # =====================================================

        base = pd.DataFrame()

        base["Cidade"] = (
            volume["Act City"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        base["Volume"] = pd.to_numeric(
            volume[periodo],
            errors="coerce"
        ).fillna(0)

        base["Premium"] = pd.to_numeric(
            premium[periodo],
            errors="coerce"
        ).fillna(0)

        # Remove linhas inválidas
        base = base[
            ~base["Cidade"].str.upper().isin(
                ["", "TOTAL", "NONE", "NAN"]
            )
        ]

        # Relevância mínima
        base = base[
            (base["Volume"] >= 50)
            &
            (base["Premium"] >= 30)
        ]

        base["% Premium"] = (
            base["Premium"]
            /
            base["Volume"].replace(0, 1)
        ) * 100

        # =====================================================
        # COBERTURA
        # =====================================================

        promotores["Cidade"] = (
            promotores["Cidade"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        hunters["Cidade"] = (
            hunters["Cidade"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        base = base.merge(
            promotores[
                ["Cidade", "Supervisor", "Qt HC"]
            ],
            on="Cidade",
            how="left"
        )

        base["Qt HC"] = (
            base["Qt HC"]
            .fillna(0)
        )

        base["Supervisor"] = (
            base["Supervisor"]
            .fillna("SEM COBERTURA")
        )

        cidades_hunter = set(
            hunters["Cidade"]
            .dropna()
            .astype(str)
            .str.strip()
        )

        base["Tem Hunter"] = (
            base["Cidade"]
            .isin(cidades_hunter)
        )

        def definir_cobertura(linha):

            if linha["Qt HC"] > 0:
                return "Com Promotor"

            if linha["Tem Hunter"]:
                return "Com Hunter"

            return "Sem Cobertura"

        base["Cobertura"] = base.apply(
            definir_cobertura,
            axis=1
        )

        # =====================================================
        # FILTROS
        # =====================================================

        cobertura_filtro = st.sidebar.selectbox(
            "Cobertura",
            [
                "Todas",
                "Com Promotor",
                "Com Hunter",
                "Sem Cobertura"
            ]
        )

        lista_supervisores = ["Todos"]

        lista_supervisores.extend(
            sorted(
                base["Supervisor"]
                .dropna()
                .unique()
            )
        )

        supervisor_filtro = st.sidebar.selectbox(
            "Supervisor",
            lista_supervisores
        )

        if cobertura_filtro != "Todas":

            base = base[
                base["Cobertura"]
                ==
                cobertura_filtro
            ]

        if supervisor_filtro != "Todos":

            base = base[
                base["Supervisor"]
                ==
                supervisor_filtro
            ]

        # =====================================================
        # KPIS
        # =====================================================

        hc_promotores = int(
            promotores["Qt HC"]
            .fillna(0)
            .sum()
        )

        hc_hunters = int(
            hunters["hunter"]
            .dropna()
            .nunique()
        )

        hc_total = (
            hc_promotores +
            hc_hunters
        )

        volume_total = int(
            base["Volume"].sum()
        )

        premium_total = int(
            base["Premium"].sum()
        )

        premium_pct = (
            premium_total
            /
            volume_total
            * 100
        ) if volume_total > 0 else 0

        qtd_cidades = (
            base["Cidade"]
            .nunique()
        )

        k1, k2, k3, k4, k5, k6, k7 = st.columns(7)

        k1.metric("Volume", f"{volume_total:,}")
        k2.metric("Premium", f"{premium_total:,}")
        k3.metric("% Premium", f"{premium_pct:.2f}%")
        k4.metric("Cidades", qtd_cidades)
        k5.metric("HC Promotores", hc_promotores)
        k6.metric("HC Hunters", hc_hunters)
        k7.metric("HC Total", hc_total)

        # =====================================================
        # ABAS
        # =====================================================

        aba1, aba2, aba3, aba4, aba5, aba6, aba7, aba8 = st.tabs([
            "📊 Resumo",
            "🏆 Ranking",
            "👨‍💼 Supervisores",
            "🎯 Cobertura",
            "🔥 Potenciais",
            "🔴 Ofensores",
            "📈 Evolução",
            "🤖 Insights"
        ])

        # =====================================================
        # RESUMO
        # =====================================================

        with aba1:

            resumo = (
                base
                .sort_values(
                    "Premium",
                    ascending=False
                )
                .head(10)
                .copy()
            )

            resumo["% Premium"] = (
                resumo["% Premium"]
                .apply(lambda x: f"{x:.2f}%")
            )

            st.dataframe(
                resumo,
                use_container_width=True
            )

        # =====================================================
        # RANKING
        # =====================================================

        with aba2:

            ranking = (
                base
                .sort_values(
                    "Premium",
                    ascending=False
                )
                .copy()
            )

            ranking["% Premium"] = (
                ranking["% Premium"]
                .apply(lambda x: f"{x:.2f}%")
            )

            st.dataframe(
                ranking,
                use_container_width=True
            )

            fig = px.bar(
                base.sort_values(
                    "Premium",
                    ascending=False
                ).head(15),
                x="Cidade",
                y="Premium",
                color="Premium",
                title="Top 15 Premium"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # =====================================================
        # SUPERVISORES
        # =====================================================

        with aba3:

            supervisor_df = (
                base
                .groupby("Supervisor")
                .agg({
                    "Volume": "sum",
                    "Premium": "sum",
                    "Qt HC": "sum"
                })
                .reset_index()
            )

            supervisor_df["% Premium"] = (
                supervisor_df["Premium"]
                /
                supervisor_df["Volume"].replace(0, 1)
            ) * 100

            supervisor_df = supervisor_df.sort_values(
                "Premium",
                ascending=False
            )

            supervisor_view = supervisor_df.copy()

            supervisor_view["% Premium"] = (
                supervisor_view["% Premium"]
                .apply(lambda x: f"{x:.2f}%")
            )

            st.dataframe(
                supervisor_view,
                use_container_width=True
            )

        # =====================================================
        # COBERTURA
        # =====================================================

        with aba4:

            cobertura_df = (
                base.groupby("Cobertura")
                .agg({
                    "Cidade": "count",
                    "Volume": "sum",
                    "Premium": "sum",
                    "Qt HC": "sum"
                })
                .reset_index()
            )

            cobertura_df.columns = [
                "Cobertura",
                "Qtd Cidades",
                "Volume",
                "Premium",
                "HC"
            ]

            st.dataframe(
                cobertura_df,
                use_container_width=True
            )

        # =====================================================
        # POTENCIAIS
        # =====================================================

        with aba5:

            potenciais = (
                base[
                    base["Cobertura"]
                    ==
                    "Sem Cobertura"
                ]
                .sort_values(
                    "Premium",
                    ascending=False
                )
            )

            if len(potenciais) == 0:

                st.success(
                    "✅ Todas as cidades elegíveis possuem cobertura."
                )

            else:

                st.dataframe(
                    potenciais,
                    use_container_width=True
                )

        # =====================================================
        # OFENSORES
        # =====================================================

        with aba6:

            media_premium = (
                base["Premium"]
                .mean()
            )

            ofensores = (
                base[
                    base["Premium"]
                    <
                    media_premium
                ]
                .sort_values("Premium")
                .copy()
            )

            ofensores["% Premium"] = (
                ofensores["% Premium"]
                .apply(lambda x: f"{x:.2f}%")
            )

            st.dataframe(
                ofensores,
                use_container_width=True
            )

        # =====================================================
        # EVOLUÇÃO
        # =====================================================

        with aba7:

            semanas = [
                "Week -6",
                "Week -5",
                "Week -4",
                "Week -3",
                "Week -2",
                "Week -1"
            ]

            evolucao = []

            for s in semanas:

                evolucao.append({
                    "Semana": s,
                    "Volume": pd.to_numeric(
                        volume[s],
                        errors="coerce"
                    ).fillna(0).sum(),
                    "Premium": pd.to_numeric(
                        premium[s],
                        errors="coerce"
                    ).fillna(0).sum()
                })

            evolucao = pd.DataFrame(evolucao)

            fig = px.line(
                evolucao,
                x="Semana",
                y=["Volume", "Premium"],
                markers=True
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            st.dataframe(
                evolucao,
                use_container_width=True
            )

        # =====================================================
        # INSIGHTS
        # =====================================================

        with aba8:

            if len(base) > 0:

                top_premium = (
                    base.sort_values(
                        "Premium",
                        ascending=False
                    ).iloc[0]
                )

                top_volume = (
                    base.sort_values(
                        "Volume",
                        ascending=False
                    ).iloc[0]
                )

                supervisor_top = (
                    base.groupby("Supervisor")
                    ["Premium"]
                    .sum()
                    .reset_index()
                    .sort_values(
                        "Premium",
                        ascending=False
                    )
                    .iloc[0]
                )

                qtd_hunter = len(
                    base[
                        base["Cobertura"]
                        ==
                        "Com Hunter"
                    ]
                )

                st.success(
                    f"🏆 {top_premium['Cidade']} lidera Premium com {int(top_premium['Premium'])} unidades."
                )

                st.info(
                    f"📦 {top_volume['Cidade']} lidera Volume com {int(top_volume['Volume'])} unidades."
                )

                st.warning(
                    f"👨‍💼 {supervisor_top['Supervisor']} lidera os supervisores com {int(supervisor_top['Premium'])} unidades Premium."
                )

                st.info(
                    f"🎯 {qtd_hunter} cidades são atendidas por Hunters com cobertura quinzenal focada em desenvolvimento de mercado."
                )

    except Exception as erro:

        st.error(f"Erro encontrado: {erro}")