from transformers import pipeline
from googletrans import Translator
from collections import Counter
import concurrent.futures


def return_dict_of_companies():
    dict = {'Ading AD Skopje': 'ADIN',
            'Agromehanika AD Skopje': 'AMEH',
            'Alkaloid AD Skopje': 'ALK',
            'Angropromet Tikvesanka AD Kavadarci': 'APTK',
            'Automakedonija AD Skopje': 'AUMK',
            'BIM AD Sveti Nikole': 'BIM',
            'Blagoj Tufanov AD Radovis': 'BLTU',
            'Cementarnica USJE AD Skopje': 'USJE',
            'Centralna kooperativna banka AD Skopje': 'CKBKO',
            'Debarski bani - Capa AD Debar': 'DEBA',
            'Dimko Mitrev AD Veles': 'DIMI',
            'DS Smith AD Skopje': 'KOMU',
            'Evropa AD Skopje': 'EVRO',
            'Fabrika Karpos AD Skopje': 'KPSS',
            'Fakom AD Skopje': 'FAKM',
            'Fersped AD Skopje': 'FERS',
            'Fruktal Mak AD Skopje': 'KONZ',
            'Fustelarko Borec AD Bitola': 'fubt',
            'FZC 11 Oktomvri AD Kumanovo': 'CEVI',
            'GD Tikves AD Kavadarci': 'tikv',
            'Geras Cunev Konfekcija AD Strumica': 'GECK',
            'Geras Cunev Trgovija AD Strumica': 'GECT',
            'Granit AD Skopje': 'GENT',
            'Grozd AD Strumica': 'GRZD',
            'GTC AD Skopje': 'GTC',
            'Hoteli-Metropol AD Ohrid': 'MPOL',
            'Internesnel Hotels AD Skopje': 'INHO',
            'Interpromet AD Tetovo': 'INPR',
            'Karpos AD Skopje': 'KPSS',
            'Klanica so ladilnik AD Strumica': 'KLST',
            'Komercijalna Banka AD Skopje': 'KMB',
            'Kristal 1923 AD Veles': 'BGOR',
            'Liberti AD Skopje': 'RZLV',
            'Lotarija na Makedonija AD Skopje': 'LOTO',
            'Makedonija osiguruvane  AD Skopje': 'KJUBI',
            'Makedonijaturist AD Skopje': 'MTUR',
            'Makedonski Telekom AD Skopje': 'TEL',
            'Makosped AD Skopje': 'MKSD',
            'Makoteks AD Skopje': 'MAKS',
            'Makpetrol AD Skopje': 'MPT',
            'Makpromet AD Stip': 'MAKP',
            'Makstil AD Skopje': 'STIL',
            'Mermeren kombinat AD Prilep': 'MERM',
            'Moda AD Sveti Nikole': 'MODA',
            'MZT Pumpi AD Skopje': 'MZPU',
            'Nemetali Ograzden AD Strumica': 'NEME',
            'NLB Banka AD Skopje': 'TNB',
            'Nova stokovna kuka AD Strumica': 'NOSK',
            'OILKO KDA Skopje': 'OILK',
            'OKTA AD Skopje': 'OKTA',
            'Oranzerii Hamzali AD Strumica': 'ORAN',
            'Patnicki soobrakaj - Transkop AD Bitola': 'TRPS',
            'Pekabesko AD Kadino, Ilinden': 'PKB',
            'Pelisterka AD Skopje': 'LOZP',
            'Popova kula AD Demir Kapija': 'POPK',
            'Prilepska pivarnica AD Prilep': 'PPIV',
            'Rade Koncar - Aparatna tehnika AD Skopje': 'RADE',
            'Replek AD Skopje': 'REPL',
            'Rudnici Banani AD Skopje': 'BANA',
            'RZ Ekonomika AD Skopje': 'RZEK',
            'RZ Inter-Transsped AD Skopje': 'RZIT',
            'RZ Tehnicka kontrola AD Skopje': 'RZTK',
            'RZ Uslugi AD Skopje': 'RZUS',
            'Sigurnosno staklo AD Prilep': 'SSPR',
            'Sileks AD Kratovo': 'SIL',
            'Skopski Pazar AD Skopje': 'SPAZP',
            'Slavej AD Skopje': 'SLAV',
            'SN Osiguritelen Broker AD Bitola': 'SNBTO',
            'Sovremen dom AD Prilep': 'SDOM',
            'Stokopromet AD Skopje': 'STOK',
            'Stopanska banka AD Bitola': 'SBT',
            'Stopanska banka AD Skopje': 'STBP',
            'Strumicko pole AD s. Vasilevo': 'SPOL',
            'Tajmiste AD Kicevo': 'TAJM',
            'TEAL AD Tetovo': 'TEAL',
            'Tehnokomerc AD Skopje': 'TEHN',
            'Teteks AD Tetovo': 'TETE',
            'Trgotekstil maloprodazba AD Skopje': 'TSMP',
            'Triglav osiguruvane AD Skopje': 'VROS',
            'Trudbenik AD Ohrid': 'TRDB',
            'TTK Banka AD Skopje': 'TTK',
            'Tutunski kombinat AD Prilep': 'TKPR',
            'Ugotur AD Skopje': 'RZUG',
            'UNI Banka AD Skopje': 'UNI',
            'Vabtek MZT AD Skopje': 'MZHE',
            'Veteks AD Veles': 'VTKS',
            'Vitaminka AD Prilep': 'VITA',
            'VV Tikves AD Kavadarci': 'TKVS',
            'ZAS AD Skopje': 'ZAS',
            'Zito Karaorman AD Kicevo': 'ZKAR',

            'Zito Luks AD Skopje': 'ZILUP',
            'Zito Polog AD Tetovo': 'ZPOG',
            'ZK Pelagonija AD Bitola': 'ZPKO'}

    dict_reversed = {value: key for key, value in dict.items()}
    additional_entries = {
        'CKB': 'Centralna kooperativna banka AD Skopje',
        'SAPZ': 'Skopski Pazar AD Skopje',
        'STB': 'Stopanska banka AD Skopje',
        'ZILU': 'Zito Luks AD Skopje',
    }

    dict_reversed.update(additional_entries)

    return dict_reversed


def translate_text(text, src_language='mk', dest_language='en'):
    try:
        translator = Translator()
        translation = translator.translate(text, src=src_language, dest=dest_language).text
        return translation
    except Exception:
        return ""


def summarize_text(text, model_name="t5-small"):
    summarizer = pipeline("summarization", model=model_name, tokenizer=model_name)
    chunks = [text[i:i + 1024] for i in range(0, len(text), 1024)]
    summaries = [summarizer(chunk, max_length=150, min_length=50, do_sample=False)[0]['summary_text'] for chunk in
                 chunks]
    return " ".join(summaries)


def analyze_sentiment(text):
    sentiment_analyzer = pipeline("sentiment-analysis", model="ProsusAI/finbert")
    result = sentiment_analyzer(text)
    return result[0]['label']


def main_function(company_name):
    file_path = f'C:/Users/User/Downloads/Proeckt/Proeckt/data/{company_name}/{company_name}.txt'
    with open(file_path, 'r', encoding='utf-8') as file:
        macedonian_text = file.read()
    if not macedonian_text.strip():
        return "Not enough data available!"
    print("\nTranslating text...")
    translated_text = translate_text(macedonian_text)
    if translated_text == "":
        return "Not enough data available!"
    print("\nSummarizing text...")
    summarized_text = summarize_text(translated_text)
    print("\nSummarized Text:\n", summarized_text)

    print("\nAnalyzing sentiment...")
    sentiment_result = analyze_sentiment(summarized_text)
    print("\nSentiment Analysis Result:", sentiment_result)
    return sentiment_result


def run_multiple_tests(company_name, num_tests=5):
    sentiment_results = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(main_function, company_name) for _ in range(num_tests)]
        for future in concurrent.futures.as_completed(futures):
            sentiment_result = future.result()
            sentiment_results.append(sentiment_result)

    sentiment_counter = Counter(sentiment_results)
    mode_sentiment = sentiment_counter.most_common(1)[0]
    print(f"THE ANALYSIS PREDICTED SENTIMENT IS {mode_sentiment[0]}")
    return mode_sentiment[0]


def main_funct(company_name='ALK'):
    company_abbreviation = return_dict_of_companies().get(company_name)
    if not company_abbreviation:
        return f"Company '{company_name}' is not found in the news dictionary."

    return run_multiple_tests(company_abbreviation, num_tests=4)


if __name__ == "__main__":
    main_funct('ALK')
