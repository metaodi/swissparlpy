import marimo

__generated_with = "0.23.16"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import swissparlpy as spp
    from swissparlpy import GeverBackend


    return GeverBackend, mo, spp


@app.cell
def _(mo):
    mo.md("""
    # Gever backend example with widgets

    This notebook makes the Swiss Parliament Gever example interactive.
    Use the controls below to switch backends, browse records, and search members.
    """)
    return


@app.cell
def _(mo):
    backend_picker = mo.ui.dropdown(
        label="Backend",
        value="Canton of Zurich",
        options={
            "Canton of Zurich": "canton_zurich",
            "City of Zurich": "city_zurich",
        },
        full_width=True,
    )
    search_term = mo.ui.text(label="Member search term", value="Marti")



    mo.vstack([backend_picker, search_term])


    return backend_picker, search_term


@app.cell
def _(backend_picker, mo, spp):
    available_tables = spp.get_tables(backend=backend_picker.value)

    table = mo.ui.dropdown(
        label="Table",
        value=available_tables[0] if available_tables else None,
        options=available_tables,
        full_width=True,
    )

    mo.vstack([table])
    return (table,)


@app.cell
def _(backend_picker, mo, spp, table):
    data = spp.get_data(table.value, backend=backend_picker.value, Language="DE")
    data_table = mo.ui.table(data)
    data_summary = mo.md(
        f"### Data for {backend_picker.value} table {table.value}\n\nShowing the first five rows."
    )
    mo.vstack([data_summary, data_table])
    return


@app.cell
def _(backend_picker, mo, search_term, spp):
    search_value = search_term.value.strip()

    print(search_value)

    if search_value:
        members = spp.get_data("Person", LastName=search_value, Language="DE", backend=backend_picker.value)
        member_table = mo.ui.table(members)

    mo.vstack([member_table])
    return


@app.cell
def _(GeverBackend, mo):
    backend = GeverBackend(instance="canton_zurich")
    member = backend.get_data("mitglieder", "Name adj Marti and Vorname adj Res")[0]
    if "foto_id" in member:
        download_link = backend.file(
            "mitglieder",
            member["foto_id"],
            member["foto_version"]["nr"],
            "Original",
        )
    else:
        download_link = "No image available"

    mo.md(
        f"""
        ### Download URL example

        The generated download link for the first matching member is:

        {download_link}
        """
    )


    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
