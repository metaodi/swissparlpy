# Drei Parlamentsdatenbanken, eine Python-Bibliothek: was swissparlpy wirklich bringt

Wer schon mal versucht hat, Abstimmungsdaten aus dem Bundeshaus zu ziehen, kennt das Gefühl: drei APIs, drei Formate, drei Arten von Kopfschmerzen. Die eidgenössische Kammer spricht OData, kantonale und kommunale Parlamente sprechen REST, und die Geschäftsverwaltungssysteme (Gever) von Kanton und Stadt Zürich sprechen wieder eine eigene Sprache mit XSD-Schemas und CQL-Queries. Wer parlamentarische Daten über mehrere Staatsebenen hinweg auswerten will, verbringt die meiste Zeit nicht mit Analyse, sondern mit dem Übersetzen zwischen Datenmodellen. **swissparlpy** räumt diesen Flickenteppich auf, indem es die drei Backends hinter einer einheitlichen Python-API versteckt: `get_tables()`, `get_variables()`, `get_data()`, `get_glimpse()` und `get_overview()` funktionieren überall gleich, das Backend wird per Parameter oder über einen `SwissParlClient` gewählt.

## Warum nicht einfach die APIs direkt ansprechen?

Die kurze Antwort: weil man es sonst dreimal macht. Die etwas längere Antwort hat vier Teile.

Erstens die **einheitliche Schnittstelle**. Der National- und Ständerat liefern Daten über einen OData-Webservice, der eher wie eine SQL-Datenbank über HTTP funktioniert. OpenParlData.ch, das kantonale und kommunale Parlamente wie Personen, Sitzungen, Voten und Geschäfte abdeckt, ist eine klassische REST-API mit Pagination und Suchparametern. Die Gever-Systeme von Kanton und Stadt Zürich wiederum liefern XML-lastige, teils tief verschachtelte Antworten, deren Struktur sich nur über ein XSD-Schema erschliesst. Drei Datenmodelle, drei Fehlerformate, drei Arten von Pagination – swissparlpy nimmt einem ab, für jedes davon einen eigenen Client zu schreiben.

Zweitens die **pandas-Integration**. Jede Antwort ist iterierbar, indexierbar, sliceable und lässt sich mit einer Zeile in ein DataFrame verwandeln (`.to_dataframe()`). Für alle, die in Python Daten auswerten, ist das der Unterschied zwischen "JSON parsen und Spalten selbst benennen" und "sofort weiterarbeiten".

Drittens die **eingebaute Fehlerbehandlung und Pagination**. Die OpenParlData-API etwa liefert Resultate seitenweise; swissparlpy folgt den `next_page`-Links transparent, sodass eine Iteration über das Resultat wirklich alle Datensätze liefert, egal welche Seitengrösse man angegeben hat. Das klingt banal, ist es aber nicht – wer das selbst implementiert, merkt schnell, wie viele Randfälle es bei Pagination, Rate-Limits und Session-Handling gibt.

Viertens die **wiederverwendbare Filterlogik**. Statt für jede Abfrage von Hand Query-Strings zu bauen, akzeptiert `get_data()` Keyword-Argumente, die je nach Backend automatisch in die passende Filtersyntax übersetzt werden – inklusive Operatoren wie `__contains`, `__startswith` oder `__gt`/`__lt` für Datumsbereiche beim OData-Backend. Wer komplexere Bedingungen braucht, kann sie auch als Python-Callable über `swissparlpy.Filter` formulieren.

## Der praktische Teil: vier Beispiele

**1. Einfache Abfrage plus DataFrame**

Der Standardfall: Parteien des Nationalrats abfragen und direkt weiterverarbeiten.

```python
import swissparlpy as spp

parties_df = spp.get_data('Party', Language='DE').to_dataframe()
print(parties_df[['Abbreviation', 'Name']].head())
```

Kein manuelles Parsen, keine Session-Verwaltung – die Zeile liefert ein fertiges DataFrame.

**2. Filterung nach Datum und Substring**

Für Auswertungen über Zeiträume oder Stichwortsuchen im Titel eines Geschäfts sind die Operatoren des OData-Backends praktisch:

```python
import swissparlpy as spp
from datetime import datetime

# Geschäfte mit "CO2" im Titel
co2_business = spp.get_data("Business", Title__contains="CO2", Language="DE")

# Vorstösse, die im Oktober 2019 eingereicht wurden
vorstoesse = spp.get_data(
    "Business",
    SubmissionDate__gt=datetime.fromisoformat('2019-09-30'),
    SubmissionDate__lte=datetime.fromisoformat('2019-10-31'),
    Language="DE",
)
```

Das erspart das manuelle Bauen von OData-Filterausdrücken und macht die Abfrage lesbar.

**3. Verwandte Daten abrufen**

Ein Alleinstellungsmerkmal des OpenParlData-Backends: Zu einer Entität wie einer Person lassen sich verlinkte Tabellen direkt nachladen, ohne die IDs manuell zu verknüpfen.

```python
import swissparlpy as spp

opd_client = spp.SwissParlClient(backend="openparldata")
person = opd_client.get_data("persons", firstname="Gerhard", lastname="Andrey")[0]

print(person.get_related_tables())
# ['memberships', 'interests', 'affairs', 'speeches', 'votes', ...]

memberships = person.get_related_data('memberships').to_dataframe()
print(memberships[["group_name_de", "role_name_de", "type_harmonized"]].head())
```

Beim Gever-Backend läuft die Verknüpfung anders: Wiederholte Felder wie Mandate einer Person werden anhand des XSD-Schemas automatisch als Listenfelder erkannt und bleiben in `to_dataframe()` zunächst als Liste-von-Dicts in einer Spalte stehen. Mit `explode()` lassen sie sich in eine eigene, flache Tabelle zerlegen – inklusive `parent_obj_guid`, um später wieder zurückzujoinen:

```python
import swissparlpy as spp

data = spp.get_data('mitglieder', backend='gever')
mandate = data.explode('behoerdenmandate')
```

Beim OData-Backend gibt es keine eingebaute Related-Data-Funktion; verwandte Tabellen (z.B. Personen und ihre Ratsmitgliedschaften) müssen über gemeinsame IDs selbst verknüpft werden, wie man es von relationalen Datenbanken kennt.

**4. Visualisierung einer Abstimmung**

Für alle, die Resultate nicht nur auswerten, sondern zeigen wollen: `plot_voting()` stellt eine Abstimmung gemäss Sitzordnung des Nationalrats dar, mit mehreren Themes.

```python
import swissparlpy as spp
import matplotlib.pyplot as plt

votes = spp.get_data("Voting", Language="DE", IdVote=23458)
fig = spp.plot_voting(votes, theme='scoreboard', result=True)
plt.show()
```

Das Extra `swissparlpy[visualization]` bringt die nötigen matplotlib-Abhängigkeiten mit.

## Wo es hakt

Ein ehrlicher Blogpost verschweigt die Grenzen nicht, und swissparlpy hat einige, die man kennen sollte, bevor man produktiv damit arbeitet.

Das **OpenParlData-Backend** ist laut eigener Dokumentation noch in Entwicklung – Endpunkte und Parameter können sich ändern, was für produktive Pipelines ein Risiko ist, das man einkalkulieren muss. Ausserdem ist `limit` bei diesem Backend keine Obergrenze, sondern eine Seitengrösse: Wer über das Resultat iteriert, lädt trotzdem alle Seiten, was bei grossen Tabellen überraschend lange dauern kann. Und `search_mode="exact"` ist entgegen der API-Dokumentation case-sensitiv – ein Detail, das leicht zu stillen, falschen Nullresultaten führt.

Beim **OData-Backend** können grosse Abfragen, insbesondere bei den Tabellen `Voting` und `Transcript`, serverseitig mit 500-Fehlern abbrechen. Die pragmatische Lösung ist, Abfragen in Batches – etwa pro Session – aufzuteilen und danach zusammenzuführen, was zusätzlichen Code erfordert, den man selbst schreiben muss.

Beim **Gever-Backend** hängt die Qualität der Daten am Schema: Ohne ladbares XSD-Schema bleibt die Verschachtelung roh, und nur ein Fallback für eine Handvoll bekannter Feldnamen greift. Wer mit unbekannten oder sich ändernden Tabellen arbeitet, muss also damit rechnen, verschachtelte Dictionaries selbst auseinanderzunehmen.

Und schliesslich: Die Sitzplatz-zu-Person-Zuordnung bei `plot_voting()` ist nicht historisiert. Wer ältere Abstimmungen visualisiert, riskiert falsch zugeordnete Sitze, da sich die Sitzordnung über die Legislaturperioden ändert. Für aktuelle Abstimmungen ist das kein Problem, für historische Analysen sollte man die Grafik mit Vorsicht lesen oder eine eigene Sitzzuordnung mitgeben.

Wer swissparlpy nicht in Python nutzen will oder kann, findet mit dem R-Paket "swissparl" und dem JS-Paket "swissparl" ähnliche Ansätze in anderen Sprachen – das Konzept einer vereinheitlichten Schnittstelle über die föderale Datenlandschaft der Schweiz ist also nicht auf ein Ökosystem beschränkt.

## Fazit

swissparlpy löst kein exotisches Problem, sondern ein sehr alltägliches: den Aufwand, den es kostet, wenn öffentliche Institutionen ihre Daten in unterschiedlichen technischen Dialekten anbieten. Genau das macht solche Tools relevant für datengetriebene Entscheidungsgrundlagen – nicht weil sie neue Daten schaffen, sondern weil sie die Hürde senken, bestehende Daten überhaupt systematisch auszuwerten. Wer politische Prozesse, Abstimmungsverhalten oder Geschäftsverläufe über Gemeinde-, Kantons- und Bundesebene hinweg vergleichen will, spart mit einer solchen Abstraktionsschicht nicht nur Zeit, sondern reduziert auch die Fehlerquellen, die beim manuellen Umgang mit drei unterschiedlichen APIs entstehen. Die Limitationen sind real und sollten vor dem produktiven Einsatz ernst genommen werden – aber als Einstiegspunkt in die Schweizer Open-Parliament-Daten ist swissparlpy ein solides, gut dokumentiertes Werkzeug, das zeigt, wie viel Open-Source-Tooling im Bereich Open Government Data leisten kann.

*Quelle und weiterführende Dokumentation: [github.com/metaodi/swissparlpy](https://github.com/metaodi/swissparlpy)*
