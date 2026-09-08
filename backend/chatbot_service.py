"""
Multilingual Chatbot Service for AgricLedger
Supports English, Shona, and Ndebele with comprehensive agricultural knowledge
Includes image analysis and real farming advice
"""

import os
import json
import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgricLedgerChatbot:
    """
    Multilingual chatbot for agricultural advisory
    Supports: English, Shona, Ndebele with extensive farming knowledge
    """
    
    def __init__(self):
        """Initialize the chatbot with comprehensive knowledge base"""
        self.languages = ['English', 'Shona', 'Ndebele']
        
        # Build comprehensive knowledge bases
        self.knowledge_base = self._build_knowledge_base()
        self.crop_info = self._build_crop_info()
        self.translations = self._build_translations()
        self.pest_info = self._build_pest_info()
        self.weather_info = self._build_weather_info()
        self.market_info = self._build_market_info()
        self.disease_info = self._build_disease_info()
        self.fertilizer_info = self._build_fertilizer_info()
        self._load_training_corpus()
        
        logger.info("✅ Advanced Multilingual Chatbot initialized with full knowledge base")
    
    def _load_training_corpus(self):
        """Load CSV training corpus for dataset-driven intent matching"""
        self.qa_corpus = []
        stop_words = {
            'what', 'when', 'where', 'which', 'who', 'whom', 'whose', 'why', 'how',
            'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did',
            'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as',
            'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
            'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under',
            'again', 'further', 'then', 'once', 'here', 'there', 'all', 'any', 'both',
            'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
            'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just',
            'should', 'now', 'chii', 'sei', 'pipi', 'ani', 'kupi', 'kuti', 'ngei',
            'yini', 'baphi', 'nini', 'kuphi', 'njani'
        }
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            corpus_path = os.path.join(base_dir, 'data', 'chatbot', 'chatbot_training.csv')
            if os.path.exists(corpus_path):
                import csv
                with open(corpus_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        kw = set(r['keywords'].lower().replace(',', ' ').split())
                        q_tokens = set(re.findall(r'\w+', r['question'].lower()))
                        all_tokens = {t for t in kw.union(q_tokens) if t not in stop_words and len(t) >= 3}
                        self.qa_corpus.append({
                            'id': r['id'],
                            'category': r['category'],
                            'language': r['language'],
                            'question': r['question'],
                            'answer': r['expected_answer'],
                            'tokens': all_tokens
                        })
                logger.info(f"Loaded {len(self.qa_corpus)} Q&A items into chatbot training corpus.")
        except Exception as e:
            logger.warning(f"Could not load chatbot training corpus: {e}")
    
    def _build_knowledge_base(self) -> Dict[str, Dict[str, str]]:
        """Build comprehensive agricultural knowledge base with real farming advice"""
        return {
            # Crop Planting
            'crop_planting': {
                'english': "The best time to plant {crop} in Zimbabwe is during the rainy season. {crop} should be planted when the soil has adequate moisture. For most crops, November to December is ideal. Always test your soil pH before planting. Use certified seeds and plant at the correct depth.",
                'shona': "Nguva yakanakisa yekudyara {crop} muZimbabwe inguva yemvura. {crop} inofanirwa kudyara kana ivhu rine hunyoro hwakakwana. Kazhinji, Mbudzi kusvika Zvita ndiyo nguva yakanaka. Gara uchiyedza ivhu rako pH usati wadyara. Shandisa mbeu dzakasimbiswa uye dyara pakadzika kwakaringana.",
                'ndebele': "Isikhathi esihle sokutshala {crop} eZimbabwe yisikhathi semvula. {crop} kufanele itshalwe lapho umhlabathi unomswakama owaneleyo. Ngokuvamile, ngoLwezi kuya kuZibandlela kuhle. Hlala uhlola i-pH yomhlabathi ngaphambi kokutshala. Sebenzisa izimbewu eziqinisekisiwe futhi utshale ekujuleni okufanele."
            },
            'soil_preparation': {
                'english': "Prepare your soil by plowing deeply (20-30cm) and adding organic manure or compost. Allow the soil to rest for 2-3 weeks before planting. Add lime if soil is too acidic (pH < 5.5) or sulfur if too alkaline (pH > 7.5). Proper soil preparation increases yields by up to 30%.",
                'shona': "Gadzirira ivhu rako nekurima zvakadzika (20-30cm) uye nekuisa mupfudze kana manyowa. Siyai ivhu rizorore kwemavhiki 2-3 usati wadyara. Wedzera lime kana ivhu rine acid (pH < 5.5) kana sulfur kana rine alkaline (pH > 7.5). Kugadzirira ivhu zvakanaka kunowedzera goho nechikamu che30%.",
                'ndebele': "Lungisa umhlabathi wakho ngokulima ngokujula (20-30cm) nokufaka umquba. Vumela umhlabathi uphumule amaviki 2-3 ngaphambi kokutshala. Faka i-lime uma umhlabathi une-asidi (pH < 5.5) noma i-sulfur uma une-alkaline (pH > 7.5). Ukulungisa umhlabathi kahle kwandisa isivuno ngo-30%."
            },
            'fertilizer': {
                'english': "Use a balanced fertilizer like Compound D (7:14:7) at planting. Top-dress with Ammonium Nitrate or Urea 4-6 weeks after planting. For organic farming, use well-decomposed manure or compost. Apply fertilizer based on soil test results for best results. Over-fertilization can damage crops.",
                'shona': "Shandisa fetiraiza yakanaka seCompound D (7:14:7) panguva yekudyara. Wedzera Ammonium Nitrate kana Urea mushure memavhiki 4-6. Kana uchirima zvisikwa, shandisa mupfudze wakaora zvakanaka. Isa fetiraiza zvichienderana nemhedzisiro yekuyedzwa kweivhu kuti uwane mhedzisiro yakanaka. Kuwedzera fetiraiza kunogona kukuvadza zvirimwa.",
                'ndebele': "Sebenzisa umanyolo olinganiselayo njengeCompound D (7:14:7) ngesikhathi sokutshala. Faka i-Ammonium Nitrate noma i-Urea ngemuva kwamaviki 4-6. Uma ulima ngokwemvelo, sebenzisa umquba obolile kahle. Faka umanyolo ngokuvumelana nemiphumela yokuhlolwa komhlabathi ukuze uthole imiphumela engcono. Ukufaka umanyolo ngokweqile kungalimaza izitshalo."
            },
            'pest_control': {
                'english': "Common pests include fall armyworm, maize stalk borer, aphids, and cutworms. Use recommended pesticides or natural methods like neem oil, garlic spray, and crop rotation. Monitor your crops regularly and take action early to prevent major damage. Healthy crops are more resistant to pests.",
                'shona': "Zvipembenene zvinowanzoitika zvinosanganisira fall armyworm, maize stalk borer, aphids, uye cutworms. Shandisa mishonga yezvipembenene kana nzira dzakasikwa senge neem oil, garlic spray, uye kutenderera zvirimwa. Tarisa zvirimwa zvako nguva dzose uye tora matanho ekutanga kudzivirira kukuvara kukuru. Zvirimwa zvine hutano zvinodzivirira zvipembenene zvakanyanya.",
                'ndebele': "Izinambuzane ezivamile zihlanganisa i-fall armyworm, i-maize stalk borer, ama-aphids, nama-cutworms. Sebenzisa izibulala-zinambuzane ezinconyiwe noma izindlela zemvelo ezifana ne-neem oil, i-garlic spray, nokushintshana izitshalo. Qaphela izitshalo zakho njalo futhi uthathe izinyathelo zakuqala ukuze uvimbele umonakalo omkhulu. Izitshalo ezinempilo zihlala nezilokazane ngaphezulu."
            },
            'harvesting': {
                'english': "Harvest when the crop is mature. Maize is ready when the husks turn brown and the grain is hard. Tobacco leaves are ready when they show yellow-green color. Harvest early in the morning to preserve quality. Handle produce carefully to prevent damage. Store in a cool, dry place.",
                'shona': "Kohwa kana chirimwa chanyatsoibva. Chibage chinoibva kana mashanga aita shava uye zviyo zvikaita kuoma. Mashizha efodya anoibva kana aita ruvara rweyero-girini. Kohwa mangwanani-ngwanani kuti uchengetedze hunhu. Bata zvirimwa zvakanyatsonaka kudzivirira kukuvara. Chengeta munzvimbo inotonhorera uye yakaoma.",
                'ndebele': "Vuna lapho isitshalo sevuthiwe. Umbila uvutha lapho amagobolondo eba nsundu kanye nokusanhla kuqina. Amacembe kafuya avutha lapho eba nombala ophuzi-luhlaza. Vuna ekuseni ukuze ugcine ikhwalithi. Phatha izitshalo ngokucophelela ukuze uvimbele umonakalo. Gcina endaweni epholile neyomile."
            },
            # Irrigation
            'irrigation': {
                'english': "Water your crops regularly, especially during dry spells. Drip irrigation is the most water-efficient method. For maize, water during flowering and grain filling stages. Avoid overwatering as it can cause root rot. Early morning or evening watering reduces evaporation.",
                'shona': "Diridza zvirimwa zvako nguva dzose, kunyanya panguva yekusanaya. Drip irrigation ndiyo nzira inoshandisa mvura zvakanaka. Kune chibage, diridza panguva yekutumbuka uye kuzara kwezviyo. Dzivisa kudiridza zvakanyanya nekuti zvinogona kukonzera kuora kwemidzi. Kudiridza mangwanani-ngwanani kana manheru kunoderedza kushanduka kwemvura.",
                'ndebele': "Nisela izitshalo zakho njalo, ikakhulukazi ngezikhathi zomile. I-drip irrigation iyona indlela esebenzisa amanzi kahle. Kumbila, nisela ngesikhathi sokuqhakaza nokugcwala kwezinhlamvu. Gwema ukunisela ngokweqile ngoba kungabangela ukubola kwezimpande. Ukunisela ekuseni noma kusihlwa kunciphisa ukuhwamuka kwamanzi."
            },
            # Climate Change
            'climate_change': {
                'english': "Climate change is affecting Zimbabwean agriculture. Use drought-resistant crop varieties, practice conservation agriculture, and adopt climate-smart practices like mulching and rainwater harvesting. Plant cover crops to protect soil during dry seasons.",
                'shona': "Kushanduka kwemamiriro ekunze kuri kukanganisa kurima muZimbabwe. Shandisa mhando dzezvirimwa dzisingaodi mvura zhinji, ita kurima kwakachengetedza, uye shandisa nzira dzakachenjera dzemamiriro ekunze senge mulch uye kuchengetedza mvura yemvura. Dyara zvirimwa zvinodzivirira ivhu munguva yekusanaya.",
                'ndebele': "Ukushintsha kwesimo sezulu kuthinta ezolimo eZimbabwe. Sebenzisa izinhlobo zezitshalo ezingabekezeleli isomiso, yenza ukulima okulondoloza, futhi usebenzise izindlela ezihlakaniphile zesimo sezulu ezifana ne-mulch nokuqoqa amanzi emvula. Tshala izitshalo ezivikela umhlabathi ngezikhathi ezomile."
            }
        }
    
    def _build_crop_info(self) -> Dict[str, Dict[str, Any]]:
        """Build comprehensive crop information with real data"""
        return {
            'maize': {
                'planting_time': 'November-December',
                'growing_period': '90-120 days',
                'ideal_temp': '18-30°C',
                'rainfall_need': '500-1200mm',
                'soil_type': 'Loam, Sandy Loam',
                'yield_expectation': '4-6 tonnes/ha',
                'common_pests': 'Fall armyworm, Stalk borer, Aphids',
                'best_regions': 'Lowveld, Midveld',
                'fertilizer': 'Compound D (7:14:7) at planting, Urea top-dressing',
                'spacing': '75cm x 30cm',
                'seed_rate': '20-25 kg/ha',
                'growing_notes': 'Plant seeds 5-7cm deep. Apply D-compound fertilizer at planting. Top dress with Urea 4-6 weeks after emergence. Water during flowering. Harvest when husks turn brown.'
            },
            'tobacco': {
                'planting_time': 'September-October',
                'growing_period': '120-150 days',
                'ideal_temp': '15-28°C',
                'rainfall_need': '600-1000mm',
                'soil_type': 'Sandy Loam',
                'yield_expectation': '2-3 tonnes/ha',
                'common_pests': 'Aphids, Cutworms, Whiteflies',
                'best_regions': 'Midveld, Highveld',
                'fertilizer': 'N-P-K fertilizer',
                'spacing': '60cm x 50cm',
                'seed_rate': '2-3 kg/ha',
                'growing_notes': 'Plant in well-drained soil. Apply N-P-K fertilizer. Irrigate during dry periods. Harvest leaves individually as they mature from bottom to top.'
            },
            'wheat': {
                'planting_time': 'May-June',
                'growing_period': '120-150 days',
                'ideal_temp': '10-25°C',
                'rainfall_need': '400-800mm',
                'soil_type': 'Loam, Clay Loam',
                'yield_expectation': '3-4 tonnes/ha',
                'common_pests': 'Aphids, Hessian fly, Rust',
                'best_regions': 'Highveld, Midveld',
                'fertilizer': 'Nitrogen in split applications',
                'spacing': '15cm row spacing',
                'seed_rate': '150-200 kg/ha',
                'growing_notes': 'Sow seeds 4-5cm deep. Apply nitrogen in split applications. Water during tillering and grain filling. Harvest when grain moisture content is 13-14%.'
            },
            'soybean': {
                'planting_time': 'November-December',
                'growing_period': '100-120 days',
                'ideal_temp': '15-30°C',
                'rainfall_need': '400-800mm',
                'soil_type': 'Loam',
                'yield_expectation': '2-3 tonnes/ha',
                'common_pests': 'Aphids, Soybean rust, Pod borers',
                'best_regions': 'Lowveld, Midveld',
                'fertilizer': 'Phosphorus fertilizer',
                'spacing': '45cm row spacing',
                'seed_rate': '80-100 kg/ha',
                'growing_notes': 'Plant seeds 3-4cm deep, 45cm apart. Inoculate with Rhizobium bacteria. Apply phosphorus fertilizer. Harvest when pods are brown and seeds are dry.'
            },
            'cotton': {
                'planting_time': 'October-November',
                'growing_period': '150-180 days',
                'ideal_temp': '20-35°C',
                'rainfall_need': '400-700mm',
                'soil_type': 'Sandy, Loam',
                'yield_expectation': '1.5-2 tonnes/ha',
                'common_pests': 'Bollworms, Aphids, Whiteflies',
                'best_regions': 'Lowveld, Midveld',
                'fertilizer': 'Balanced NPK fertilizer',
                'spacing': '90cm x 30cm',
                'seed_rate': '10-15 kg/ha',
                'growing_notes': 'Plant seeds 3-5cm deep. Apply balanced fertilizer. Water during flowering and boll formation. Harvest when bolls open fully.'
            },
            'groundnuts': {
                'planting_time': 'November-December',
                'growing_period': '120-150 days',
                'ideal_temp': '18-30°C',
                'rainfall_need': '500-1000mm',
                'soil_type': 'Sandy Loam',
                'yield_expectation': '1-1.5 tonnes/ha',
                'common_pests': 'Aphids, Thrips, Leaf spot',
                'best_regions': 'Lowveld, Midveld',
                'fertilizer': 'Lime, Phosphorus',
                'spacing': '45cm x 15cm',
                'seed_rate': '80-100 kg/ha',
                'growing_notes': 'Plant seeds 5-8cm deep. Apply lime if acidic. Water moderately. Harvest when pods mature and shells have a dark brown color.'
            },
            'sorghum': {
                'planting_time': 'November-December',
                'growing_period': '120-150 days',
                'ideal_temp': '20-35°C',
                'rainfall_need': '300-600mm',
                'soil_type': 'Sandy, Loam',
                'yield_expectation': '2-3 tonnes/ha',
                'common_pests': 'Shoot fly, Stem borer, Aphids',
                'best_regions': 'Lowveld, Midveld',
                'fertilizer': 'Nitrogen fertilizer',
                'spacing': '75cm x 20cm',
                'seed_rate': '10-15 kg/ha',
                'growing_notes': 'Plant seeds 3-5cm deep. Apply nitrogen. Water during establishment and flowering. Harvest when grains are hard and moisture content is below 14%.'
            },
            'sunflower': {
                'planting_time': 'October-November',
                'growing_period': '120-150 days',
                'ideal_temp': '15-30°C',
                'rainfall_need': '400-700mm',
                'soil_type': 'Loam, Sandy',
                'yield_expectation': '1.5-2 tonnes/ha',
                'common_pests': 'Sunflower moth, Aphids, Cutworms',
                'best_regions': 'Lowveld, Midveld',
                'fertilizer': 'Phosphorus and Potassium',
                'spacing': '75cm x 25cm',
                'seed_rate': '5-8 kg/ha',
                'growing_notes': 'Plant seeds 4-6cm deep. Apply phosphorus and potassium. Water during flowering. Harvest when back of flower head turns brown.'
            },
            'sweetpotato': {
                'planting_time': 'October-December',
                'growing_period': '120-150 days',
                'ideal_temp': '15-28°C',
                'rainfall_need': '500-1200mm',
                'soil_type': 'Sandy Loam',
                'yield_expectation': '10-15 tonnes/ha',
                'common_pests': 'Sweetpotato weevil, Aphids',
                'best_regions': 'Lowveld, Midveld',
                'fertilizer': 'Potassium-rich fertilizer',
                'spacing': '30cm x 30cm',
                'seed_rate': '30,000-40,000 cuttings/ha',
                'growing_notes': 'Plant cuttings 20-30cm long. Apply potassium-rich fertilizer. Water during establishment. Harvest 4-5 months after planting.'
            },
            'cassava': {
                'planting_time': 'October-November',
                'growing_period': '240-360 days',
                'ideal_temp': '15-35°C',
                'rainfall_need': '500-2000mm',
                'soil_type': 'Sandy, Loam',
                'yield_expectation': '15-20 tonnes/ha',
                'common_pests': 'Cassava mosaic virus, Mealybugs',
                'best_regions': 'Lowveld, Midveld',
                'fertilizer': 'Organic manure',
                'spacing': '100cm x 80cm',
                'seed_rate': '10,000-15,000 cuttings/ha',
                'growing_notes': 'Plant stem cuttings 10-15cm long. Apply organic manure. Plant during rainy season. Harvest 8-12 months after planting.'
            }
        }
    
    def _build_pest_info(self) -> Dict[str, Dict[str, str]]:
        """Build pest identification and control information"""
        return {
            'fall_armyworm': {
                'english': "Fall armyworm attacks maize and other cereals. Symptoms: irregular holes in leaves, frass in whorls. Control with recommended insecticides like Lambda-cyhalothrin or natural methods like neem oil. Scout fields regularly and destroy egg masses.",
                'shona': "Fall armyworm inorwisa chibage nezvimwe zviyo. Zviratidzo: maburi asina kujairika pamashizha, tsvina mumashizha. Dzidzora nemishonga inorwisa zvipembenene seLambda-cyhalothrin kana nzira dzakasikwa senge neem oil. Tarisa minda nguva dzose uye paradza mazai.",
                'ndebele': "I-fall armyworm ihlasela umbila nezinye izinhlamvana. Izimpawu: izimbobo ezingajwayelekile emacembeni, ukungcola emacembeni. Yila ngezibulala-zinambuzane ezifana ne-Lambda-cyhalothrin noma izindlela zemvelo ezifana ne-neem oil. Hlola amasimu njalo futhi ucekise amaqanda."
            },
            'aphids': {
                'english': "Aphids suck plant sap and can transmit viruses. Symptoms: curled, yellowed leaves, sticky honeydew on leaves. Control with insecticidal soap, neem oil, or natural predators like ladybirds. Remove heavily infested plant parts.",
                'shona': "Aphids inoyamwa mvura yemiti uye inogona kuparadzira hutachiona. Zviratidzo: mashizha akakombama, ane ruvara rweyero, huchi hunonamira pamashizha. Dzidzora nesipo inouraya zvipembenene, neem oil, kana zvikara zvisikwa senge ladybirds. Bvisa zvikamu zvezvirimwa zvakanyanya.",
                'ndebele': "Ama-aphids amunca umunyu wezitshalo futhi angadlulisa amagciwane. Izimpawu: amacembe agoqiwe, aphuzi, uju olunamathelayo emacembeni. Yila nge-insecticidal soap, i-neem oil, noma izilwane ezidla ezinye ezifana nama-ladybirds. Sula izingxenye zezitshalo ezithinteke kakhulu."
            }
        }
    
    def _build_weather_info(self) -> Dict[str, Dict[str, str]]:
        """Build weather advisory information"""
        return {
            'drought': {
                'english': "During drought, conserve soil moisture by mulching, use drought-tolerant crop varieties, and practice conservation agriculture. Consider irrigation if available and plant early-maturing varieties. Reduce tillage to preserve soil moisture.",
                'shona': "Munguva yekusanaya, chengetedza hunyoro hwevhu nekushandisa mulch, shandisa mhando dzezvirimwa dzisingaodi mvura zhinji, uye ita kurima kwakachengetedza. Funga nezvekudiridza kana zvichibvira uye dyara mhando dzinokurumidza kuibva. Deredza kurima kuchengetedza hunyoro hwevhu.",
                'ndebele': "Ngesikhathi sokomela, gcina umswakama womhlabathi ngokusebenzisa i-mulch, sebenzisa izinhlobo zezitshalo ezibekezelela isomiso, futhi yenza ukulima okulondoloza. Cabanga ngokunisela uma kungenzeka futhi utshale izinhlobo ezivutha ngokushesha. Nciphisa ukulima ukuze ugcine umswakama womhlabathi."
            },
            'flooding': {
                'english': "Flooding can damage crops. Plant on raised beds or ridges, improve drainage, and choose flood-tolerant varieties. After flooding, assess damage and replant if necessary. Remove debris and allow soil to dry before replanting.",
                'shona': "Mafashamo anogona kukuvadza zvirimwa. Dyara pamibhedha yakasimudzwa kana mumakomba, gadzirisa nzira dzekudonha kwemvura, uye sarudza mhando dzinoshivirira mafashamo. Mushure memafashamo, ongorora kukuvara uye dyara zvakare kana zvichidikanwa. Bvisa marara uye rega ivhu riome usati wadyara zvakare.",
                'ndebele': "Izikhukhula zingalimaza izitshalo. Tshala ezindaweni eziphakeme noma emiqolweni, lungisa imisele yokuhamba kwamanzi, futhi ukhethe izinhlobo ezibekezelela izikhukhula. Ngemuva kwezikhukhula, hlola umonakalo futhi utshale kabusha uma kudingeka. Sula imfucumfucu futhi uvumele umhlabathi wome ngaphambi kokutshala kabusha."
            }
        }
    
    def _build_market_info(self) -> Dict[str, Dict[str, str]]:
        """Build market information"""
        return {
            'market_access': {
                'english': "To access profitable markets, join a farmer cooperative, use the AgricLedger market dashboard, and ensure your produce meets quality standards. Build relationships with buyers and processors. Start with local markets before expanding.",
                'shona': "Kuti uwane misika inobatsira, pinda muboka revarimi, shandisa dashboard yemusika yeAgricLedger, uye ita kuti zvirimwa zvako zvizadze zviyero zvehunhu. Vaka hukama nevatengi nevagadziri. Tanga nemisika yemuno usati wawedzera.",
                'ndebele': "Ukuze uthole izimakethe ezinenzuzo, joyina inhlangano yabalimi, sebenzisa i-dashboard yemakethe ye-AgricLedger, futhi uqinisekise ukuthi izitshalo zakho zihlangabezana namazinga ekhwalithi. Yakha ubudlelwano nabathengi nabacubunguli. Qala ngezimakethe zendawo ngaphambi kokwandisa."
            },
            'pricing': {
                'english': "Check current market prices on the AgricLedger market dashboard. Prices vary by season and quality. Sell when prices are high, store properly when prices are low, and negotiate collectively through your cooperative. Quality products command premium prices.",
                'shona': "Tarisa mitengo yemusika yazvino pabhodhi remusika reAgricLedger. Mitengo inosiyana zvichienderana nemwaka nehunhu. Tengesa kana mitengo yakakwira, chengeta zvakanaka kana mitengo yakaderera, uye taurirana pamwe kuburikidza neboka rako. Zvigadzirwa zvehunhu zvinotenga mitengo yepamusoro.",
                'ndebele': "Hlola amanani amanje emakethe ku-dashboard yemakethe ye-AgricLedger. Amanani ayahluka ngesizini kanye nekhwalithi. Thengisa lapho amanani ephezulu, gcina kahle lapho amanani ephansi, futhi xoxisana ngokuhlanganyela ngenhlangano yakho. Imikhiqizo esezingeni eliphezulu ithola amanani aphezulu."
            }
        }
    
    def _build_disease_info(self) -> Dict[str, Dict[str, str]]:
        """Build crop disease information"""
        return {
            'maize_rust': {
                'english': "Maize rust appears as small, brownish-orange pustules on leaves. Control with resistant varieties, fungicide application, and good crop rotation. Remove infected leaves to prevent spread.",
                'shona': "Maize rust inoonekwa sezvipembenene zvidiki, zvebrown-orange pamashizha. Dzidzora nemhando dzinodzivirira, kushandisa fungicide, uye kutenderera zvirimwa. Bvisa mashizha ane hutachiona kudzivirira kupararira.",
                'ndebele': "I-maize rust ibonakala njengezilonda ezincane, ezinsundu-orenji emacembeni. Yila ngezinhlobo ezimelana, ukusebenzisa i-fungicide, nokushintshana izitshalo. Susa amacembe anesifo ukuze uvimbele ukusabalala."
            }
        }
    
    def _build_fertilizer_info(self) -> Dict[str, Dict[str, str]]:
        """Build fertilizer information"""
        return {
            'compound_d': {
                'english': "Compound D (7:14:7) is a balanced fertilizer suitable for many crops. It contains 7% Nitrogen, 14% Phosphorus, and 7% Potassium. Apply at planting rate of 300-400 kg/ha for maize. Phosphorus promotes root development and flowering.",
                'shona': "Compound D (7:14:7) fetiraiza yakanaka inokodzera zvirimwa zvakawanda. Ine 7% Nitrogen, 14% Phosphorus, uye 7% Potassium. Isa panguva yekudyara chiyero che300-400 kg/ha yechibage. Phosphorus inokurudzira kukura kwemidzi uye kutumbuka.",
                'ndebele': "I-Compound D (7:14:7) ingumanyolo olinganiselayo ofanele izitshalo eziningi. Iqukethe u-7% we-Nitrogen, u-14% we-Phosphorus, no-7% we-Potassium. Faka ngesikhathi sokutshala nge-300-400 kg/ha kumbila. I-Phosphorus ikhuthaza ukukhula kwezimpande nokuqhakaza."
            }
        }
    
    def _build_translations(self) -> Dict[str, Dict[str, str]]:
        """Build translations for common phrases"""
        return {
            'hello': {
                'english': "Hello! I'm your AgricLedger AI Assistant. How can I help you with your farming today?",
                'shona': "Mhoro! Ini ndiri Mubatsiri wako weAgricLedger AI. Ndingakubatsira sei nekurima kwako nhasi?",
                'ndebele': "Sawubona! Ngingumeli wakho we-AgricLedger AI. Ngingakusiza kanjani ngokulima kwakho namuhla?"
            },
            'thank_you': {
                'english': "You're welcome! Happy farming! Feel free to ask me anything about agriculture.",
                'shona': "Zvakanaka! Mufare kurima! Usaze usandibvunza chero chinhu nezvekurima.",
                'ndebele': "Kulungile! Jabulela ukulima! Ungangabazi ukungibuza noma yini ngezolimo."
            },
            'image_analyzed': {
                'english': "I've analyzed your image. Here's what I found:",
                'shona': "Ndaongorora mufananidzo wako. Hezvino zvandakawana:",
                'ndebele': "Ngihlaziye isithombe sakho. Nansi engikutholile:"
            },
            'image_not_clear': {
                'english': "I couldn't clearly analyze the image. Please upload a clearer photo with good lighting.",
                'shona': "Handina kukwanisa kuongorora mufananidzo zvakanaka. Ndokumbira utumire mufananidzo wakajeka une mwenje wakanaka.",
                'ndebele': "Angikwazanga ukuhlaziya isithombe kahle. Ngicela ulayishe isithombe esicacile esinokukhanya okuhle."
            }
        }
    
    def get_response(self, message: str, language: str = 'English') -> Dict[str, Any]:
        """
        Get chatbot response for a user message
        
        Args:
            message: User's message
            language: Language to respond in (English, Shona, Ndebele)
            
        Returns:
            Dict with response and metadata
        """
        message = message.lower().strip()
        language = language.capitalize()
        
        # Normalize language
        if language not in self.languages:
            language = 'English'
        
        # Check for greetings (exact word boundary match for short greetings)
        msg_tokens = set(re.findall(r'\w+', message.lower()))
        greetings = {'hello', 'hi', 'hei', 'mhoro', 'sawubona', 'bonjour'}
        if msg_tokens.intersection(greetings) and len(msg_tokens) <= 3:
            return {
                'success': True,
                'response': self.translations['hello'][language.lower()],
                'language': language,
                'intent': 'greeting'
            }
        
        # Check for thank you
        if any(word in message for word in ['thank', 'thanks', 'ndatenda', 'ngiyabonga']):
            return {
                'success': True,
                'response': self.translations['thank_you'][language.lower()],
                'language': language,
                'intent': 'thanks'
            }
        
        # Check for Q&A corpus match
        corpus_match = self._match_corpus(message, language)
        if corpus_match:
            return corpus_match

        # Check for specific crop questions
        crop_match = self._detect_crop(message)
        if crop_match:
            return self._get_crop_response(crop_match, language)
        
        # Check for pest questions
        pest_match = self._detect_pest(message)
        if pest_match and pest_match in self.pest_info:
            return {
                'success': True,
                'response': self.pest_info[pest_match][language.lower()],
                'language': language,
                'intent': 'pest_info'
            }
        
        # Check for disease questions
        disease_match = self._detect_disease(message)
        if disease_match and disease_match in self.disease_info:
            return {
                'success': True,
                'response': self.disease_info[disease_match][language.lower()],
                'language': language,
                'intent': 'disease_info'
            }
        
        # Check for topic-based responses
        topic = self._detect_topic(message)
        if topic and topic in self.knowledge_base:
            # Handle crop placeholder
            response = self.knowledge_base[topic][language.lower()]
            if '{crop}' in response:
                # Try to find a crop in the message
                crop_found = self._detect_crop(message)
                if crop_found:
                    response = response.replace('{crop}', crop_found.capitalize())
                else:
                    response = response.replace('{crop}', 'your crops')
            return {
                'success': True,
                'response': response,
                'language': language,
                'intent': topic
            }
        
        # Default response
        return {
            'success': True,
            'response': self._get_default_response(language),
            'language': language,
            'intent': 'general'
        }
    
    def get_enhanced_response(self, message: str, language: str = 'English', image_analysis: Optional[Dict] = None) -> str:
        """
        Get enhanced response with optional image analysis
        
        Args:
            message: User's message
            language: Language to respond in
            image_analysis: Image analysis results
            
        Returns:
            String response
        """
        # Get base response
        result = self.get_response(message, language)
        response = result.get('response', '')
        
        # Add image analysis if present
        if image_analysis:
            analysis_text = "\n\n" + self.translations['image_analyzed'][language.lower()]
            response = analysis_text + "\n" + response
            
            if image_analysis.get('has_pest'):
                response += "\n\n🔍 I detected possible pest issues in your image. Check for pests on the leaves and stem."
            if image_analysis.get('has_disease'):
                response += "\n\n🔍 I detected possible disease symptoms. Look for discoloration or spots."
        
        return response
    
    def _match_corpus(self, message: str, language: str) -> Optional[Dict[str, Any]]:
        """Matches user query against dataset-driven Q&A corpus using token overlap & subword matching"""
        if not hasattr(self, 'qa_corpus') or not self.qa_corpus:
            return None
            
        stop_words = {
            'what', 'when', 'where', 'which', 'who', 'whom', 'whose', 'why', 'how',
            'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did',
            'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as',
            'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
            'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under',
            'again', 'further', 'then', 'once', 'here', 'there', 'all', 'any', 'both',
            'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
            'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just',
            'should', 'now', 'chii', 'sei', 'pipi', 'ani', 'kupi', 'kuti', 'ngei',
            'yini', 'baphi', 'nini', 'kuphi', 'njani'
        }
        
        msg_text = message.lower().strip()
        raw_tokens = set(re.findall(r'\w+', msg_text))
        msg_tokens = {t for t in raw_tokens if t not in stop_words and len(t) >= 3}
        if not msg_tokens:
            return None
            
        best_item = None
        max_score = 0.0
        
        for item in self.qa_corpus:
            content_match_score = 0.0
            for t in msg_tokens:
                for item_t in item['tokens']:
                    if t == item_t:
                        content_match_score += 1.0
                        break
                    elif len(t) >= 5 and len(item_t) >= 5 and (t in item_t or item_t in t):
                        content_match_score += 0.5
                        break
                        
            if content_match_score > 0:
                total_score = content_match_score
                if item['language'].lower() == language.lower():
                    total_score += 1.0
                if total_score > max_score:
                    max_score = total_score
                    best_item = item
                
        if max_score >= 1.5 and best_item:
            answer = best_item['answer']
            if best_item['language'].lower() != language.lower():
                q_id_prefix = best_item['id'].split('-')[0]
                lang_code = 'EN' if language.lower() == 'english' else ('SN' if language.lower() == 'shona' else 'ND')
                target_id = f"{q_id_prefix}-{lang_code}-tr"
                for target_item in self.qa_corpus:
                    if target_item['id'] == target_id:
                        answer = target_item['answer']
                        break
                        
            return {
                'success': True,
                'response': answer,
                'language': language,
                'intent': best_item['category'],
                'confidence': round(min(1.0, max_score / 5.0), 2)
            }
        return None

    def _detect_crop(self, message: str) -> Optional[str]:
        """Detect if message mentions a specific crop"""
        crops = ['maize', 'tobacco', 'wheat', 'soybean', 'cotton', 
                 'groundnuts', 'sorghum', 'sunflower', 'sweetpotato', 
                 'cassava', 'chibage', 'fodya', 'gorosi']
        
        for crop in crops:
            if crop in message:
                crop_map = {
                    'chibage': 'maize',
                    'fodya': 'tobacco',
                    'gorosi': 'wheat'
                }
                return crop_map.get(crop, crop)
        return None
    
    def _detect_pest(self, message: str) -> Optional[str]:
        """Detect if message mentions a specific pest"""
        pests = ['fall armyworm', 'aphids', 'cutworms', 'stalk borer', 'whiteflies']
        for pest in pests:
            if pest in message:
                return pest.replace(' ', '_')
        return None
    
    def _detect_disease(self, message: str) -> Optional[str]:
        """Detect if message mentions a disease"""
        diseases = ['maize rust', 'soybean rust', 'cassava mosaic']
        for disease in diseases:
            if disease in message:
                return disease.replace(' ', '_')
        return None
    
    def _detect_topic(self, message: str) -> Optional[str]:
        """Detect the topic of the message"""
        topics = {
            'planting': ['plant', 'seed', 'sow', 'grow', 'kudyara', 'ukutshala'],
            'soil': ['soil', 'dirt', 'ground', 'ivhu', 'umhlabathi'],
            'fertilizer': ['fertilizer', 'manure', 'compost', 'fetiraiza', 'umanyolo'],
            'pest': ['pest', 'insect', 'bug', 'fall armyworm', 'zvipembenene', 'izinambuzane'],
            'harvest': ['harvest', 'collect', 'pick', 'kohwa', 'ukuvuna'],
            'weather': ['weather', 'rain', 'sun', 'frost', 'drought', 'mvura', 'izulu'],
            'land': ['land', 'tenure', 'title', 'deed', 'lease', 'vhu', 'umhlaba'],
            'market': ['market', 'price', 'sell', 'buy', 'customer', 'musika', 'imakethe'],
            'data': ['data', 'privacy', 'access', 'share', 'blockchain', 'data', 'idatha'],
            'money': ['loan', 'credit', 'bank', 'finance', 'money', 'kiredhiti', 'imali'],
            'irrigation': ['water', 'irrigate', 'dry', 'kudiridza', 'ukunisela'],
            'climate_change': ['climate', 'change', 'drought', 'flood', 'global warming', 'kushanduka', 'ukushintsha']
        }
        
        for topic, keywords in topics.items():
            if any(keyword in message for keyword in keywords):
                return topic
        
        return None
    
    def _get_crop_response(self, crop: str, language: str) -> Dict[str, Any]:
        """Get comprehensive crop-specific response"""
        crop_info = self.crop_info.get(crop, {})
        
        if not crop_info:
            return {
                'success': True,
                'response': self._get_default_response(language),
                'language': language,
                'intent': 'crop_not_found'
            }
        
        # Build comprehensive response based on language
        if language == 'English':
            response = f"📋 {crop.upper()} Comprehensive Guide:\n\n"
            response += f"🌱 Planting Time: {crop_info.get('planting_time', 'N/A')}\n"
            response += f"📅 Growing Period: {crop_info.get('growing_period', 'N/A')}\n"
            response += f"🌡️ Ideal Temperature: {crop_info.get('ideal_temp', 'N/A')}\n"
            response += f"💧 Rainfall Needed: {crop_info.get('rainfall_need', 'N/A')}\n"
            response += f"🧪 Best Soil: {crop_info.get('soil_type', 'N/A')}\n"
            response += f"📊 Expected Yield: {crop_info.get('yield_expectation', 'N/A')}\n"
            response += f"🐛 Common Pests: {crop_info.get('common_pests', 'N/A')}\n"
            response += f"🌍 Best Regions: {crop_info.get('best_regions', 'N/A')}\n"
            response += f"🧪 Fertilizer: {crop_info.get('fertilizer', 'N/A')}\n"
            response += f"📏 Spacing: {crop_info.get('spacing', 'N/A')}\n"
            response += f"🌱 Seed Rate: {crop_info.get('seed_rate', 'N/A')}\n\n"
            response += f"📝 Growing Notes:\n{crop_info.get('growing_notes', 'N/A')}"
            
        elif language == 'Shona':
            response = f"📋 {crop.upper()} Nhungamiro Yakazara:\n\n"
            response += f"🌱 Nguva yekudyara: {crop_info.get('planting_time', 'N/A')}\n"
            response += f"📅 Nguva yekukura: {crop_info.get('growing_period', 'N/A')}\n"
            response += f"🌡️ Tembiricha yakanaka: {crop_info.get('ideal_temp', 'N/A')}\n"
            response += f"💧 Mvura inodiwa: {crop_info.get('rainfall_need', 'N/A')}\n"
            response += f"🧪 Ivhu rakanaka: {crop_info.get('soil_type', 'N/A')}\n"
            response += f"📊 Zviri kutarisirwa: {crop_info.get('yield_expectation', 'N/A')}\n"
            response += f"🐛 Zvipembenene: {crop_info.get('common_pests', 'N/A')}\n"
            response += f"🌍 Nzvimbo dzakanaka: {crop_info.get('best_regions', 'N/A')}\n"
            response += f"🧪 Fetiraiza: {crop_info.get('fertilizer', 'N/A')}\n"
            response += f"📏 Nzvimbo: {crop_info.get('spacing', 'N/A')}\n"
            response += f"🌱 Mbeu: {crop_info.get('seed_rate', 'N/A')}\n\n"
            response += f"📝 Zvinyorwa zvekukura:\n{crop_info.get('growing_notes', 'N/A')}"
            
        else:  # Ndebele
            response = f"📋 {crop.upper()} Umhlahlandlela Ophelele:\n\n"
            response += f"🌱 Isikhathi sokutshala: {crop_info.get('planting_time', 'N/A')}\n"
            response += f"📅 Isikhathi sokukhula: {crop_info.get('growing_period', 'N/A')}\n"
            response += f"🌡️ Ukushisa okuhle: {crop_info.get('ideal_temp', 'N/A')}\n"
            response += f"💧 Imvula edingekayo: {crop_info.get('rainfall_need', 'N/A')}\n"
            response += f"🧪 Umhlabathi omuhle: {crop_info.get('soil_type', 'N/A')}\n"
            response += f"📊 Ukulindeleka: {crop_info.get('yield_expectation', 'N/A')}\n"
            response += f"🐛 Izinambuzane: {crop_info.get('common_pests', 'N/A')}\n"
            response += f"🌍 Izifunda ezinhle: {crop_info.get('best_regions', 'N/A')}\n"
            response += f"🧪 Umanyolo: {crop_info.get('fertilizer', 'N/A')}\n"
            response += f"📏 Isikhala: {crop_info.get('spacing', 'N/A')}\n"
            response += f"🌱 Imbewu: {crop_info.get('seed_rate', 'N/A')}\n\n"
            response += f"📝 Amanothi okukhula:\n{crop_info.get('growing_notes', 'N/A')}"
        
        return {
            'success': True,
            'response': response,
            'language': language,
            'intent': 'crop_info',
            'crop': crop
        }
    
    def _get_default_response(self, language: str) -> str:
        """Get default response when no specific topic is detected"""
        defaults = {
            'english': "I understand you're asking about farming. I can help with crop planting advice, soil preparation, pest control, weather information, land tenure, market access, and data sovereignty. Please ask me a specific question! I can also analyze photos of your crops.",
            'shona': "Ndinonzwisisa kuti uri kubvunza nezvekurima. Ndinogona kukubatsira nezvekurima, kugadzirira ivhu, kurwisa zvipembenene, mamiriro ekunze, kodzero dzevhu, misika, uye data. Ndokumbira undibvunze mubvunzo wakananga! Ini ndinogonawo kuongorora mifananidzo yezvirimwa zvako.",
            'ndebele': "Ngiyaqonda ukuthi ubuza ngolimo. Ngingakusiza ngokutshala, ukulungisa umhlabathi, izinambuzane, izulu, amalungelo omhlaba, imakethe, kanye nedatha. Ngicela ungibuze umbuzo oqondile! Ngingakwazi nokuhlaziya izithombe zezitshalo zakho."
        }
        return defaults.get(language.lower(), defaults['english'])


# Create singleton instance
chatbot = AgricLedgerChatbot()