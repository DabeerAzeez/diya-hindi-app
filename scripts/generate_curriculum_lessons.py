"""
Pre-generate curriculum lessons A2-01 through A2-08 and B1-01 through B1-07.
Generates both .json and .md files in diya/data/lessons/ and updates diya/data/lessons_index.json.
"""

import os
import json
import uuid

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'diya', 'data')
LESSONS_DIR = os.path.join(DATA_DIR, 'lessons')
INDEX_FILE = os.path.join(DATA_DIR, 'lessons_index.json')

import re
import sys

# Ensure UTF-8 output encoding for Windows terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def slugify(code, title):
    # Remove 'Lesson XX-XX:' prefix
    clean_title = re.sub(r'^Lesson\s+[A-Za-z0-9\.\-]+:\s*', '', title)
    clean_title = clean_title.lower()
    for ch in [':', ',', '(', ')', '"', "'", '🏷️', '&', '→', '/', '—', '-']:
        clean_title = clean_title.replace(ch, ' ')
    parts = clean_title.split()
    slug_title = '___'.join(parts) if len(parts) <= 2 else '_'.join(parts)
    # Match standard format: lesson_code__title
    code_slug = code.lower().replace('.', '_')
    return f"lesson_{code_slug}__{'_'.join(parts)}"


# Definition of the 15 lessons with rich data
LESSON_SPECS = [
    # --- LEVEL A2 ---
    {
        "code": "A2-01",
        "title": "Lesson A2-01: Compound Verbs & Aspectual Nuances",
        "level": "A2",
        "summary": "Swagat hai Level A2 ke pehle milestone par: **Compound Verbs & Aspectual Nuances**! Natural spoken Hindi mein sirf simple verbs use karna mechanical lagta hai. Native speakers action ki completion, direction aur attitude express karne ke liye verb stems ke saath explanatory auxiliaries (*Lenaa, Denaa, Jaanaa, Daalnaa*) jodte hain.",
        "polyglot": [
            ("Tamil Inward/Outward Verb Parallels:", "Tamil mein *kol/vittu* auxiliaries (jaise *saaptukko* vs *koduthuvidu*) bilkul Hindi ke *-lenaa* (inward) aur *-denaa* (outward) se match karte hain."),
            ("Romance Aspectual Reflexives:", "French/Spanish reflexive completion (*se prendre / s'en aller / llevarse*) exactly Hindi compound verbs ki tarah action ki nuance badalti hai.")
        ],
        "formulas": [
            r"\text{Verb Stem} + \text{Lenaa} \quad (\text{Self-directed / Inward benefit})",
            r"\text{Verb Stem} + \text{Denaa} \quad (\text{Other-directed / Outward action})",
            r"\text{Verb Stem} + \text{Jaanaa} \quad (\text{Completion / Change of State})",
            r"\text{Verb Stem} + \text{Daalnaa} \quad (\text{Sudden / Forceful / Decisive})"
        ],
        "sections": [
            {
                "title": "🎯 1. -Lenaa (Self-Benefit & Inward Orientation)",
                "content": [
                    "Jab action subject khud ke liye ya inward completion ke saath karta hai, toh stem ke baad **Lenaa** use hota hai:",
                    "* *Khaa lo* (Eat it up / Enjoy your food) vs *Khaao* (plain command)",
                    "* *Samajh liyaa* (Understood it thoroughly) vs *Samajhaa*",
                    "* *Soch lo* (Think it over carefully for yourself)",
                    "* *Rakh lo* (Keep it with you / retain it)"
                ]
            },
            {
                "title": "🚀 2. -Denaa (Outward Direction & Benefit to Others)",
                "content": [
                    "Jab action kisi doosre person ki taraf directed ho ya deliver ki jaa rahee ho, toh **Denaa** auxiliary aati hai:",
                    "* *Bataa do* (Tell them / Inform them)",
                    "* *Bhej diyaa* (Sent it out / Dispatched)",
                    "* *Samjhaa diyaa* (Explained it to someone else)",
                    "* *Call kar do* (Place a call to someone)"
                ]
            },
            {
                "title": "🔄 3. -Jaanaa (Permanent Completion & Transformation)",
                "content": [
                    "State change, physical movement, ya irrevocable completion ke liye **Jaanaa** stem ke saath judta hai:",
                    "* *Ho gayaa* (It got done / Finished!)",
                    "* *Chalaa gayaa* (He left / Went away completely)",
                    "* *Aa gayaa* (Arrived / Reached safely)",
                    "* *Bhool gayaa* (Forgot completely)"
                ]
            },
            {
                "title": "⚡ 4. -Daalnaa (Decisive, Forceful & Dramatic Completion)",
                "content": [
                    "Bold decisions ya urgent, rapid completion ke liye colloquial **Daalnaa** use hota hai:",
                    "* *Kar daalaa* (Got it done decisively / powered through!)",
                    "* *Bol daalaa* (Spoke out boldly / let the cat out of the bag)",
                    "* *Khatam kar daalo* (Finish it once and for all)"
                ]
            }
        ],
        "dialogue": [
            ("Shivani", "Arre! Maine sochaa ki tum abhi tak Toronto mein busy hoge. Project kaisaa chal rahaa hai?"),
            ("You", "Project final phase mein aa gayaa hai! Kal maine saara critical code deploy kar diyaa aur saare test cases run kar daale."),
            ("Shivani", "Wah yaar! Yeh sunkar achhaa lagaa. Ab October reunion plan finalise kar lo!"),
            ("You", "Bilkul! Flight tickets book kar lii hain, ab bas Norwich aane kaa wait kar rahaa hoon.")
        ],
        "quiz_concepts": [
            ("*-Lenaa* aur *-Denaa* auxiliary verbs mein kyaa foundational difference hai?",
             "**Answer:** *-Lenaa* action ko subject ke inward benefit ya personal retention ke liye orient karta hai (*Maine note kar liyaa* = I noted it down for myself), jabki *-Denaa* action ko external / outward direction mein deliver karta hai (*Maine use note de diyaa* = I gave the note away to him)."),
            ("Khabar sunne ke baad \"Maine bol diyaa\" aur \"Maine bol daalaa\" ke emotional tone mein kyaa farq hai?",
             "**Answer:** *\"Maine bol diyaa\"* ek neutral completion hai (\"I told them\"), jabki *\"Maine bol daalaa\"* ek bold, impulsive, ya decisive act denote karta hai (\"I went ahead and just blurted it out / put it out there decisively\").")
        ],
        "quiz_translations": [
            ("I have understood the whole system design thoroughly. (informal, m)",
             "`Maine pooraa system design achhe se samajh liyaa hai.` — मैंने पूरा सिस्टम डिज़ाइन अच्छे से समझ लिया है।",
             "[Maine (I [ergative]) + pooraa system design + achhe se (thoroughly) + samajh liyaa hai (have understood [compound inward])]."),
            ("Please send the cafe address to Shivani on WhatsApp. (polite)",
             "`Kripya Shivani ko WhatsApp par cafe kaa address bhej dijiye.` — कृपया शिवानी को व्हाट्सएप पर कैफ़े का एड्रेस भेज दीजिए।",
             "[Kripya (please) + Shivani ko + WhatsApp par + cafe kaa address + bhej dijiye (please send outward)]."),
            ("Don't worry, the meeting has already concluded. (casual)",
             "`Chintaa mat karo, meeting pehle hi khatam ho gayii hai.` — चिंता मत करो, मीटिंग पहले ही खत्म हो गई है।",
             "[Chintaa mat karo (don't worry) + meeting + pehle hi (already) + khatam ho gayii hai (has ended/completed [fem])]."),
            ("I finally finished that difficult coding task yesterday! (informal, m)",
             "`Maine kal aakhirkaar vo mushkil coding task khatam kar daalaa!` — मैंने कल आखिरकार वह मुश्किल कोडिंग टास्क खत्म कर डाला!",
             "[Maine + kal (yesterday) + aakhirkaar (finally) + vo mushkil coding task + khatam kar daalaa (finished decisively)]."),
            ("Keep this piano music sheet with you. (casual)",
             "`Yeh piano music sheet apne paas rakh lo.` — यह पियानो म्यूजिक शीट अपने पास रख लो।",
             "[Yeh + piano music sheet + apne paas (with yourself) + rakh lo (keep for yourself)].")
        ]
    },

    {
        "code": "A2-02",
        "title": "Lesson A2-02: Complex Sentence Structures & Correlatives",
        "level": "A2",
        "summary": "Is lesson mein hum master karenge Hindi ke classic **Correlative Structures** (*Jo...Vo, Jahaan...Vahaan, Jab...Tab*). Correlatives do dependent clauses ko link karte hain, jisse aapke sentences elementary se transition hokar sophisticated polyglot fluency achieve karte hain.",
        "polyglot": [
            ("Tamil Relative Clause Parallels:", "Tamil mein participle relative clauses (*edhu...adhu, eppo...appo*) Hindi ke *Jo...vo* aur *Jab...tab* ke exact semantic twins hain."),
            ("Romance Relative Pronouns:", "French (*celui qui...celui-là*) aur Spanish (*el que...ese*) correlative framing se bilkul align hote hain.")
        ],
        "formulas": [
            r"\text{Jo} + [\text{Condition}] \dots \text{Vo} + [\text{Result}] \quad (\text{The one who / that which})",
            r"\text{Jahaan} + [\text{Place A}] \dots \text{Vahaan} + [\text{Place B}] \quad (\text{Where \dots there})",
            r"\text{Jab} + [\text{Time A}] \dots \text{Tab} + [\text{Time B}] \quad (\text{When \dots then})",
            r"\text{Jitnaa} + [\text{Quantity A}] \dots \text{Utnaa} + [\text{Quantity B}] \quad (\text{As much as \dots that much})"
        ],
        "sections": [
            {
                "title": "🔗 1. Jo...Vo (Relative Pronouns)",
                "content": [
                    "*Jo* introduces the relative clause, aur *Vo* main clause mein target point karta hai:",
                    "* *Jo log hard work karte hain, vo successful hote hain.* (Those people who work hard are successful.)",
                    "* *Jo guitar maine Toronto mein khareedaa thaa, vo bohot achhaa hai.* (The guitar that I bought in Toronto is very good.)"
                ]
            },
            {
                "title": "📍 2. Jahaan...Vahaan & Jab...Tab (Spatial & Temporal)",
                "content": [
                    "* **Spatial:** *Jahaan Shivani rahtii hai, vahaan kaafi green parks hain.* (Where Shivani lives, there are many green parks.)",
                    "* **Temporal:** *Jab hum free honge, tab pub chalenge.* (When we are free, then we will go to the pub.)"
                ]
            },
            {
                "title": "⚖️ 3. Jitnaa...Utnaa & Jaise...Vaise (Proportion & Manner)",
                "content": [
                    "* **Proportion:** *Jitnii practice karoge, utnii fluency aayegii.* (As much practice as you do, that much fluency will come.)",
                    "* **Manner:** *Jaise improv mein quick think karte hain, vaise hi code mein adapt hotaa hoon.*"
                ]
            }
        ],
        "dialogue": [
            ("Shivani", "Jab tum UK aaoge, tab hum Norwich Castle zaroor dekhne jaayenge!"),
            ("You", "Bilkul! Jahaan tum kahogii, hum vahaan chalenge. Jo bhi local cafes achhe hain, sab explore karenge."),
            ("Shivani", "Sahi baat hai! Jitnaa time milegaa, utnaa ghoomenge.")
        ],
        "quiz_concepts": [
            ("Correlative pairs mein 'J-' words aur 'V-' words mein kyaa conceptual role distribution hoti hai?",
             "**Answer:** 'J-' words (*Jo, Jahaan, Jab, Jitnaa, Jaise*) relative/subordinate clause shuru karte hain (the condition/context), jabki 'V-' words (*Vo, Vahaan, Tab, Utnaa, Vaise*) demonstrative/main clause mein answer ya conclusion provide karte hain."),
            ("Agar 'Agar' clause mein ho, toh response clause mein kyaa connector aataa hai?",
             "**Answer:** *Agar* ke saath response clause mein **toh** aataa hai (*Agar aap ready hain, toh hum start karte hain*).")
        ],
        "quiz_translations": [
            ("The friend who lives in Norwich used to study engineering with me. (informal, m)",
             "`Jo dost Norwich mein rahtii hai, vo mere saath engineering padhtii thee.` — जो दोस्त नॉर्विच में रहती है, वह मेरे साथ इंजीनियरिंग पढ़ती थी।",
             "[Jo dost (the friend who) + Norwich mein rahtii hai + vo (she) + mere saath + engineering padhtii thee]."),
            ("When the model training completes, then we will review the output. (polite)",
             "`Jab model training complete hogii, tab hum output review karenge.` — जब मॉडल ट्रेनिंग कम्पलीट होगी, तब हम आउटपुट रिव्यू करेंगे।",
             "[Jab (when) + model training complete hogii + tab (then) + hum output review karenge]."),
            ("The more Hindi you speak daily, the more confident you will feel. (informal, m)",
             "`Jitnii zyaadaa Hindi aap daily bolenge, utnaa hi confident feel karenge.` — जितनी ज़्यादा हिंदी आप डेली बोलेंगे, उतना ही कॉन्फ़िडेंट फील करेंगे।",
             "[Jitnii zyaadaa (as much more) + Hindi aap daily bolenge + utnaa hi (that much indeed) + confident feel karenge]."),
            ("Where there is good music, people naturally gather there. (general)",
             "`Jahaan achhaa music hotaa hai, vahaan log naturally gather hote hain.` — जहाँ अच्छा म्यूजिक होता है, वहाँ लोग नेचुरली गैदर होते हैं।",
             "[Jahaan (where) + achhaa music hotaa hai + vahaan (there) + log naturally gather hote hain]."),
            ("Do the task in whatever way feels most comfortable to you. (casual)",
             "`Jaise tumhe sabse comfortable lage, vaise hi task karo.` — जैसे तुम्हें सबसे कम्फ़र्टेबल लगे, वैसे ही टास्क करो।",
             "[Jaise (in whichever way) + tumhe sabse comfortable lage + vaise hi (just in that way) + task karo].")
        ]
    },

    {
        "code": "A2-03",
        "title": "Lesson A2-03: Core Descriptive Adjectives, Sensory Qualities & Polar Opposites 🏷️ (Vocabulary Anchor 1)",
        "level": "A2",
        "summary": "Is Vocabulary Anchor milestone mein hum master karenge high-frequency spoken adjectives, sensory descriptions, aur polar opposites. Real conversations mein cheezon ki quality, temperature, size, speed aur texture accurately describe karna fluency ka key building block hai.",
        "polyglot": [
            ("Adjective Agreement Rules:", "Hindi ke marked adjectives (*-aa*) target noun ke gender aur number ke hisaab se inflect hote hain (*badaa kamraa, bade kamre, badii car*), bilkul Spanish/French agreements ki tarah."),
            ("Tamil Quality Stems:", "Tamil adjectival prefixes (*periya/siriya, nalla/ketta*) ki tarah Hindi adjectives direct noun ke aage place hote hain.")
        ],
        "formulas": [
            r"\text{Marked Adjective} (-aa / -e / -ii) + \text{Noun Agreement}",
            r"\text{Unmarked Adjective} (\text{invariant: saaf, tez, garam}) + \text{Any Noun}"
        ],
        "sections": [
            {
                "title": "🌡️ 1. Temperature & Taste Opposites",
                "content": [
                    "* **Garam** (Hot) vs **Thandaa** (Cold): *Garam chaay* vs *Thandaa paani*",
                    "* **Meethaa** (Sweet) vs **Teekhaa** (Spicy/Piquant): *Meethii lassi* vs *Teekhaa street food*",
                    "* **Kaddvaa** (Bitter) vs **Khattā** (Sour)"
                ]
            },
            {
                "title": "📏 2. Dimension, Weight & Distance",
                "content": [
                    "* **Badaa** (Big) vs **Chhotaa** (Small): *Badaa room* vs *Chhotii car*",
                    "* **Bhaari** (Heavy) vs **Halkaa** (Light): *Bhaari luggage* vs *Halkaa bag*",
                    "* **Door** (Far) vs **Paas** (Near): *Norwich London se kaafi door hai.*"
                ]
            },
            {
                "title": "⚡ 3. Speed, Difficulty & Quality",
                "content": [
                    "* **Tez** (Fast/Sharp) vs **Dheere** (Slow): *Tez drive mat karo.*",
                    "* **Aasaan** (Easy) vs **Mushkil** (Difficult): *Hindi grammar aasaan hai!*",
                    "* **Saaf** (Clean) vs **Gandaa** (Dirty)",
                    "* **Mehengaa** (Expensive) vs **Sastaa** (Cheap)"
                ]
            }
        ],
        "dialogue": [
            ("Shivani", "Yeh cafe kaisaa lagaa? Yahaan ki coffee kaafi garam aur tasty hai na?"),
            ("You", "Haan, bilkul! Aur atmosphere bhi kaafi shaant aur saaf hai. Toronto ke crowded cafes se kaafi alag hai."),
            ("Shivani", "Sahi baat hai. Norwich thodaa chhotaa shehar hai, isliye life yahaan halkii aur aasaan lagtii hai.")
        ],
        "quiz_concepts": [
            ("Marked adjectives (jaise *badaa*, *mehengaa*) aur Unmarked adjectives (jaise *saaf*, *tez*) mein inflection kaa kyaa difference hai?",
             "**Answer:** Marked adjectives feminine noun ke saath *-ii* aur plural/oblique masculine ke saath *-e* ban jaate hain (*badaa/bade/badii*), jabki Unmarked adjectives kisi bhi gender ya number ke aage invariant rahte hain (*saaf kamraa, saaf mezein, saaf sadak*)."),
            ("Agar koi item 'mehengaa' hai, toh discount maangte waqt bargaining mein kaun sa opposite word use karte hain?",
             "**Answer:** *Sastaa* (cheap/inexpensive) ya *\"Thodaa sastaa lagaaiye / kam kijiye\"*.")
        ],
        "quiz_translations": [
            ("This hot tea is very sweet, but I prefer less sugar. (informal, m)",
             "`Yeh garam chaay bohot meethii hai, lekin main kam cheeni prefer kartaa hoon.` — यह गरम चाय बहुत मीठी है, लेकिन मैं कम चीनी प्रेफ़र करता हूँ।",
             "[Yeh + garam chaay (hot tea [fem]) + bohot meethii hai (very sweet) + lekin (but) + main kam cheeni prefer kartaa hoon]."),
            ("That suitcase is too heavy, please lift this light bag instead. (polite)",
             "`Vo suitcase bohot bhaari hai, kripya iske bajaay yeh halkaa bag uthaaiye.` — वह सूटकेस बहुत भारी है, कृपया इसके बजाय यह हल्का बैग उठाइए।",
             "[Vo suitcase bohot bhaari hai + kripya (please) + iske bajaay (instead of this) + yeh halkaa bag uthaaiye]."),
            ("Is learning Hindi grammar easy or difficult for you? (casual)",
             "`Kyaa Hindi grammar seekhnaa aapke liye aasaan hai ya mushkil?` — क्या हिंदी ग्रामर सीखना आपके लिए आसान है या मुश्किल?",
             "[Kyaa + Hindi grammar seekhnaa + aapke liye + aasaan (easy) + hai ya (or) + mushkil (difficult)?]"),
            ("We walked on a clean and quiet street near the river. (informal, m)",
             "`Hum river ke paas ek saaf aur shaant sadak par chale.` — हम रिवर के पास एक साफ़ और शांत सड़क पर चले।",
             "[Hum + river ke paas (near the river) + ek saaf aur shaant sadak par + chale (walked)]."),
            ("This new tech gadget is quite expensive, but it saves a lot of time. (informal, m)",
             "`Yeh naya tech gadget kaafi mehengaa hai, lekin bohot time bachaataa hai.` — यह नया टेक गैजेट काफ़ी महंगा है, लेकिन बहुत टाइम बचाता है।",
             "[Yeh naya tech gadget + kaafi mehengaa hai (quite expensive) + lekin + bohot time bachaataa hai].")
        ]
    },

    {
        "code": "A2-04",
        "title": "Lesson A2-04: Dative Experiencer Frameworks (Lagnaa, Aanaa, Pataa, Yaad)",
        "level": "A2",
        "summary": "Hindi grammar ka sabse powerful aur distinctive pillar hai **Dative Experiencer Framework**. In structures mein insaan action ka 'doer' (agent) nahin hotaa, balki sensation, skill ya memory ka 'recipient' (experiencer) ban jaataa hai. Isliye subject hamesha **Ko / Mujhe** leta hai.",
        "polyglot": [
            ("Tamil Enakku Mirror:", "Tamil mein *Enakku theriyum* (I know), *Enakku theriyadhu* (I don't know), *Enakku nyabagam irukku* (I remember) Hindi ke *Mujhe pataa hai, Mujhe yaad hai* se 1-to-1 correspond karte hain."),
            ("Romance Indirect Experiencers:", "Spanish (*Me gusta / Me parece / Me duele*) aur French (*Il me faut*) exact dative experiencer alignment follow karte hain.")
        ],
        "formulas": [
            r"\text{Experiencer} + \text{ko} + \text{Sensations/State} + \text{Lagnaa} \quad (\text{bhookh, pyaas, thand, achhaa})",
            r"\text{Experiencer} + \text{ko} + \text{Skill/Language} + \text{Aanaa} \quad (\text{French aatii hai, coding aataa hai})",
            r"\text{Experiencer} + \text{ko} + \text{Fact/Info} + \text{Pataa honaa} \quad (\text{Mujhe pataa hai ki\dots})",
            r"\text{Experiencer} + \text{ko} + \text{Memory} + \text{Yaad aanaa} \quad (\text{Mujhe university ke din yaad aate hain})"
        ],
        "sections": [
            {
                "title": "🍽️ 1. Bodily & Emotional Sensations with Lagnaa",
                "content": [
                    "* *Mujhe bhookh lag rahii hai.* (I am feeling hungry.)",
                    "* *Mujhe pyaas lagii hai.* (I feel thirsty.)",
                    "* *Mujhe thand lag rahii hai.* (I am feeling cold.)",
                    "* *Mujhe buraa lagaa.* (I felt bad about it.)"
                ]
            },
            {
                "title": "🎸 2. Skills & Languages with Aanaa",
                "content": [
                    "Hindi mein skills aapse belong karte hain: 'Skill comes to me':",
                    "* *Mujhe guitar bajanaa aataa hai.* (I know how to play guitar.)",
                    "* *Mujhe French aur Spanish aatii hain.* (I know French and Spanish - languages take feminine agreement).",
                    "* *Kyaa aapko coding aatii hai?* (Do you know coding?)"
                ]
            },
            {
                "title": "💭 3. Knowledge & Memories (Pataa vs Yaad)",
                "content": [
                    "* **Pataa honaa:** *Mujhe pataa hai ki Shivani Norwich mein hai.* (I know that...)",
                    "* **Yaad aanaa:** *Mujhe Toronto ke snow storms yaad aate hain.* (I remember / miss Toronto snow storms.)",
                    "* *Mujhe aapka naam yaad hai.* (I remember your name.)"
                ]
            }
        ],
        "dialogue": [
            ("Shivani", "Tumhe bhookh lag rahii hai kyaa? Paas mein ek bohot achhaa Thai restaurant hai."),
            ("You", "Haan yaar, mujhe kaafi bhookh lagii hai! Vaise, kyaa tumhe spicy food pasand hai?"),
            ("Shivani", "Bohot! Aur mujhe pataa hai ki tumhe teekhaa khaanaa bohot achhaa lagtaa hai."),
            ("You", "Sahi baat hai! University days yaad aa rahe hain jab hum midnight ko noodles banaate the.")
        ],
        "quiz_concepts": [
            ("Language skills express karte waqt verb agreement kiske hisaab se hoti hai? (e.g. 'Mujhe French aatii hai')",
             "**Answer:** Verb language ke grammatical gender se agree karti hai. Hindi mein saari languages feminine maani jaati hain (*French, Hindi, English, Tamil*), isliye verb hamesha feminine singular *-tii hai* ya plural *-tii hain* hotii hai."),
            ("'Mujhe yaad hai' aur 'Mujhe yaad aayaa' mein kyaa aspectual difference hai?",
             "**Answer:** *\"Mujhe yaad hai\"* ek continuous state of knowledge hai (\"I remember / I have it in memory\"), jabki *\"Mujhe yaad aayaa\"* ek sudden moment of recall denote karta hai (\"It just came to my mind / I just remembered!\").")
        ],
        "quiz_translations": [
            ("I know how to play the piano and guitar. (informal, m)",
             "`Mujhe piano aur guitar bajanaa aataa hai.` — मुझे पियानो और गिटार बजाना आता है।",
             "[Mujhe (to me) + piano aur guitar + bajanaa (to play) + aataa hai (comes)]."),
            ("Do you remember our university improv rehearsals? (casual, to Shivani)",
             "`Kyaa tumhe humaare university improv rehearsals yaad hain?` — क्या तुम्हें हमारे यूनिवर्सिटी इम्प्रोव रिहर्सल्स याद हैं?",
             "[Kyaa + tumhe (to you casual) + humaare university improv rehearsals + yaad hain (are remembered)]."),
            ("I feel cold here, please close the window. (polite)",
             "`Mujhe yahaan thand lag rahii hai, kripya khidkii band kar dijiye.` — मुझे यहाँ ठंड लग रही है, कृपया खिड़की बंद कर दीजिए।",
             "[Mujhe yahaan + thand lag rahii hai (cold is feeling) + kripya + khidkii band kar dijiye]."),
            ("We don't know what time the pub closes. (informal)",
             "`Humein nahin pataa ki pub kitne baje band hotaa hai.` — हमें नहीं पता कि पब कितने बजे बंद होता है।",
             "[Humein (to us) + nahin pataa (not known) + ki + pub kitne baje band hotaa hai]."),
            ("She knows four different languages fluently. (respectful/female peer)",
             "`Unhein chaar alag-alag languages fluently aatii hain.` — उन्हें चार अलग-अलग लैंग्वेजेस फ़्लूएंसी से आती हैं।",
             "[Unhein (to her respectful) + chaar alag-alag languages + fluently aatii hain].")
        ]
    },

    {
        "code": "A2-05",
        "title": "Lesson A2-05: The Hinglish Code-Switching Architecture & English Backup Strategies",
        "level": "A2",
        "summary": "Modern metropolitan India aur global diaspora mein natural communication ka gold standard **Spoken Hinglish** hai. Is lesson mein hum Hinglish ki inner architecture decode karenge: kaun se English words plug-in ho sakte hain aur kaun sa Hindi grammatical scaffolding non-negotiable hai.",
        "polyglot": [
            ("Taglish & Franglais Parallels:", "Global urban bilinguals (Manila, Montreal, Paris) exactly isi tarah nouns borrow karte hain jabki verb conjugation native language mein anchor rahti hai."),
            ("Tamil-English Code Mixing:", "Tamil speakers jis tarah *'Pannu'* ya *'Aachu'* add karke *manage pannu* bolte hain, Hindi mein wahi engine *Karnaa / Honaa* hai.")
        ],
        "formulas": [
            r"\text{English Verb/Noun} + \text{Karnaa} \quad (\text{Active: decide karnaa, message karnaa})",
            r"\text{English Verb/Noun} + \text{Honaa} \quad (\text{Passive/State: cancel honaa, start honaa})",
            r"\text{English Adjective} + \text{Lagnaa / Feel honaa} \quad (\text{Sensory: weird lagnaa, awkward lagnaa})"
        ],
        "sections": [
            {
                "title": "🏗️ 1. Safe Loanwords vs Non-Negotiable Hindi Scaffolding",
                "content": [
                    "* **Safe to insert in English:** Nouns (*meeting, laptop, project, tickets, flight*), modern adjectives (*busy, stressed, exciting, cool*), tech terms.",
                    "* **Never replace with English:** Postpositions (*me, se, par, ke liye*), pronouns (*main, aap, mujhe, unhone*), obliques, tense auxiliaries (*thaa, hai, rahe hain*)."
                ]
            },
            {
                "title": "⚙️ 2. The Conjunct Verb Engine",
                "content": [
                    "* **Active:** *Main meeting schedule kar rahaa hoon.*",
                    "* **Passive/Involuntary:** *Flight cancel ho gayii.*",
                    "* **Sensory/Impression:** *Yeh plan thodaa risky lag rahaa hai.*"
                ]
            },
            {
                "title": "🧩 3. Compound Verbs on English Stems",
                "content": [
                    "* *Call kar do* (Call them outward)",
                    "* *Check kar lo* (Check it for yourself)",
                    "* *File save kar lii* (Saved the file safely)",
                    "* *Feature deploy kar diyaa* (Deployed the feature)"
                ]
            }
        ],
        "dialogue": [
            ("Shivani", "Tumhaari flight landing ke baad mujhe text message bhej denaa, theek hai?"),
            ("You", "Haan, main land hote hi message send kar doongaa. Vaise train ticket book kar liyaa hai?"),
            ("Shivani", "Haan, advance mein reserve kar liyaa thaa taaki price increase na ho. Bilkul hassle-free trip hogii!")
        ],
        "quiz_concepts": [
            ("English words borrow karte waqt gender assignment ka spoken Hindi rule kyaa hai?",
             "**Answer:** Generally physical objects, devices, aur technical items masculine hote hain (*phone, laptop, project, code*), jabki processes, communication formats, abstract concepts, aur drinks often feminine hote hain (*coffee, meeting, email, file, call*)."),
            ("Agar English stem ke baad 'karnaa' ke badle 'honaa' use kiyaa jaaye, toh sentence structure mein kyaa change aataa hai?",
             "**Answer:** *Karnaa* active agent structure banata hai (*Maine decide kiyaa*), jabki *Honaa* non-agentive ya involuntary state banata hai (*Decide ho gayaa* / *Plan cancel ho gayaa*).")
        ],
        "quiz_translations": [
            ("Please check your email and confirm the appointment. (polite)",
             "`Kripya apnii email check kar lijiye aur appointment confirm kar dijiye.` — कृपया अपनी ईमेल चेक कर लीजिए और अपॉइंटमेंट कन्फ़र्म कर दीजिए।",
             "[Kripya + apnii email check kar lijiye (check for yourself) + aur appointment confirm kar dijiye (confirm outward)]."),
            ("The AI team is currently testing this new model update. (informal, m)",
             "`AI team abhi is naye model update ko test kar rahii hai.` — AI टीम अभी इस नए मॉडल अपडेट को टेस्ट कर रही है।",
             "[AI team + abhi (currently) + is naye model update ko + test kar rahii hai]."),
            ("It felt very awkward when the zoom call suddenly disconnected. (informal)",
             "`Jab zoom call achaanak disconnect ho gayaa, toh kaafi awkward lagaa.` — जब ज़ूम कॉल अचानक डिस्कनेक्ट हो गया, तो काफ़ी ऑकवर्ड लगा।",
             "[Jab zoom call + achaanak (suddenly) + disconnect ho gayaa + toh kaafi awkward lagaa]."),
            ("Can you please share the Google maps location with me? (polite)",
             "`Kyaa aap mere saath Google maps location share kar sakte hain?` — क्या आप मेरे साथ गूगल मैप्स लोकेशन शेयर कर सकते हैं?",
             "[Kyaa aap + mere saath + Google maps location + share kar sakte hain?]."),
            ("I have already downloaded all the offline maps for Norwich. (informal, m)",
             "`Maine Norwich ke saare offline maps pehle hi download kar liye hain.` — मैंने नॉर्विच के सारे ऑफलाइन मैप्स पहले ही डाउनलोड कर लिए हैं।",
             "[Maine + Norwich ke saare offline maps + pehle hi (already) + download kar liye hain (downloaded for myself)].")
        ]
    },

    {
        "code": "A2-06",
        "title": "Lesson A2-06: High-Yield Spoken Action Verbs & Practical Movement 🏷️ (Vocabulary Anchor 2)",
        "level": "A2",
        "summary": "Daily life, travel, aur spontaneous meetup situations mein physical objects ko handle karna aur dynamic movement describe karna essential hotaa hai. Is lesson mein hum high-yield physical action verbs (*Rakhnaa, Uthaanaa, Chhodnaa, Pakadnaa, Sambhaalnaa*) master karenge.",
        "polyglot": [
            ("Intransitive vs Transitive Movement Pairs:", "Spanish (*quedarse vs dejar*) aur Tamil (*nillu vs niruthu*) ki tarah Hindi mein *Ruknaa* (to pause/stop oneself) vs *Roknaa* (to stop something externally) pair hota hai."),
            ("Object Holding Idioms:", "Tamil *pidi* (to catch/hold) Hindi *Pakadnaa* se perfectly match karta hai.")
        ],
        "formulas": [
            r"\text{Intransitive (Self)}: \text{Ruknaa (to stop)}, \text{Girnaa (to fall)}, \text{Bachnaa (to survive)}",
            r"\text{Transitive (Caused)}: \text{Roknaa (to stop sth)}, \text{Giraanaa (to drop)}, \text{Bachaanaa (to save)}"
        ],
        "sections": [
            {
                "title": "📦 1. Handling Objects & Physical Belongings",
                "content": [
                    "* **Rakhnaa:** *Yeh bag table par rakh do.* (Put this bag on the table.)",
                    "* **Uthaanaa:** *Heavy box mat uthaao.* (Don't lift the heavy box.)",
                    "* **Chhodnaa:** *Mujhe station par chhod denaa.* (Drop me off at the station.)",
                    "* **Pakadnaa:** *Meraa phone pakdo ek minute.* (Hold my phone for a second.)"
                ]
            },
            {
                "title": "🚶 2. Transit, Arrival & Searching",
                "content": [
                    "* **Pahunchnaa:** *Main 10 minutes mein pahunchūngaa.* (I will arrive in 10 minutes.)",
                    "* **Dhoondhnaa:** *Main apnii keys dhoondh rahaa hoon.* (I am looking for my keys.)",
                    "* **Milnaa:** *Keys mil gayiin!* (The keys were found!)",
                    "* **Chalaanaa:** *Gaadi dhyaan se chalaao.* (Drive the car carefully.)"
                ]
            },
            {
                "title": "🛡️ 3. Managing & Taking Care",
                "content": [
                    "* **Sambhaalnaa:** *Fikar mat karo, main sab sambhaal loongaa.* (Don't worry, I will manage / handle everything.)",
                    "* *Yeh documents sambhaal kar rakhnaa.* (Keep these documents safely.)"
                ]
            }
        ],
        "dialogue": [
            ("Shivani", "Station pahunch kar mujhe call karnaa, main tumhe pick karne aa jaaoongii."),
            ("You", "Main train mein baith gayaa hoon aur 4 baje tak pahunchūngaa. Apnaa phone paas rakhnaa!"),
            ("Shivani", "Bilkul! Luggage sambhaal kar uthaanaa, platform par bheed ho saktii hai."),
            ("You", "Haan, fikar mat karo, main easily manage kar loongaa.")
        ],
        "quiz_concepts": [
            ("'Ruknaa' aur 'Roknaa' mein kyaa conceptual farq hai?",
             "**Answer:** *Ruknaa* intransitive hai jisme subject khud thahar jaata hai (*Hum red light par ruke* = We stopped), jabki *Roknaa* transitive hai jisme subject kisi doosri cheez ko rokta hai (*Police ne car ko rokaa* = Police stopped the car)."),
            ("Searching action 'Dhoondhnaa' aur finding outcome 'Milnaa' mein grammatical structure kaise badaltaa hai?",
             "**Answer:** *Dhoondhnaa* active transitive verb hai jo subject dwara ki jaati hai (*Main phone dhoondh rahaa hoon*), jabki *Milnaa* dative/passive result hai jisme object mil jaata hai (*Mujhe phone mil gayaa*).")
        ],
        "quiz_translations": [
            ("Please drop me off near the Norwich city library. (polite)",
             "`Kripya mujhe Norwich city library ke paas chhod dijiye.` — कृपया मुझे नॉर्विच सिटी लाइब्रेरी के पास छोड़ दीजिए।",
             "[Kripya mujhe + Norwich city library ke paas + chhod dijiye (please drop off)]."),
            ("Hold my jacket for a moment while I tie my shoes. (casual)",
             "`Ek minute meri jacket pakdo jab tak main apne joote baandh loon.` — एक मिनट मेरी जैकेट पकड़ो जब तक मैं अपने जूते बाँध लूँ।",
             "[Ek minute meri jacket pakdo (hold my jacket) + jab tak (while) + main apne joote baandh loon]."),
            ("I was looking for my guitar picks everywhere and finally found them. (informal, m)",
             "`Main har jagah apne guitar picks dhoondh rahaa thaa aur aakhirkaar mil gaye.` — मैं हर जगह अपने गिटार पिक्स ढूँढ रहा था और आखिरकार मिल गए।",
             "[Main har jagah + apne guitar picks dhoondh rahaa thaa + aur aakhirkaar mil gaye]."),
            ("Don't worry about the dinner preparations, I will handle everything. (informal, m)",
             "`Dinner preparations ki chintaa mat karo, main sab sambhaal loongaa.` — डिनर प्रिपरेशन्स की चिंता मत करो, मैं सब संभाल लूँगा।",
             "[Dinner preparations ki chintaa mat karo + main sab sambhaal loongaa]."),
            ("What time will your train reach the central station? (polite)",
             "`Aapki train kitne baje central station pahunchegii?` — आपकी ट्रेन कितने बजे सेंट्रल स्टेशन पहुँचेगी?",
             "[Aapki train + kitne baje + central station pahunchegii?].")
        ]
    },

    {
        "code": "A2-07",
        "title": "Lesson A2-07: The Subjunctive Mood, Permissions & Hypothetical Situations",
        "level": "A2",
        "summary": "Subjunctive mood language mein uncertainty, suggestions, polite offers, aur hypothetical wishes express karne ke liye use hotaa hai. Is lesson mein hum *'Main bolūn?'*, *'Kyaa hum chalein?'* se lekar *'Kaash aisaa hotaa!'* tak master karenge.",
        "polyglot": [
            ("Romance Subjunctive Roots:", "French (*Que je parle / Qu'on aille*) aur Spanish (*Que hablemos / Ojalá*) subjunctive Hindi optative suffixes (*-oon, -e, -ein*) se exact match karte hain."),
            ("Tamil Suggestive Suffixes:", "Tamil *-laamaa* (jaise *Polaamaa?* = Shall we go?) Hindi subjunctive *Chalein?* ke identical hai.")
        ],
        "formulas": [
            r"\text{Suggestive Question}: \text{Main / Hum} + \text{Verb Stem} + [-\bar{u}\text{n} / -\text{ein}]?",
            r"\text{Hypothetical / Wish}: \text{Kaash} + \text{Subject} + \text{Verb Stem} + \text{taa / te / tii}",
            r"\text{Unreal Condition}: \text{Agar} + [\text{Past Habitual}] \dots \text{Toh} + [\text{Past Habitual}]"
        ],
        "sections": [
            {
                "title": "🙋 1. Polite Offers & Suggestive Questions",
                "content": [
                    "Future endings *-ūngaa / -enge* se assertive commitment banta hai, lekin subjunctive *-oon / -ein* se polite collaborative suggestion banta hai:",
                    "* *Main order karūn?* (Shall I order? / Should I place the order?)",
                    "* *Kyaa hum chalein?* (Shall we leave now?)",
                    "* *Main Shivani ko phone lagaoon?* (Should I call Shivani?)"
                ]
            },
            {
                "title": "🌟 2. Wishes & Regrets with 'Kaash'",
                "content": [
                    "Jab aap wish karte hain ki situation different hotii, toh **Kaash** + past habitual stem lagta hai:",
                    "* *Kaash hum har weekend mil sakte!* (I wish we could meet every weekend!)",
                    "* *Kaash mere paas thodaa aur time hotaa.* (I wish I had a bit more time.)"
                ]
            },
            {
                "title": "💭 3. Counterfactual Unreal Conditionals",
                "content": [
                    "Agar past hypothetical situation discuss karni ho:",
                    "* *Agar main Norwich mein hotaa, toh hum weekly jam sessions karte.* (If I were in Norwich, we would do weekly jam sessions.)",
                    "* *Agar weather achhaa hotaa, toh hum garden mein baithte.*"
                ]
            }
        ],
        "dialogue": [
            ("Shivani", "Table ready hai! Kyaa main dono ke liye drinks order karūn?"),
            ("You", "Haan zaroor! Aur agar pub food achhaa ho, toh kuch snacks bhi mangwaa lete hain."),
            ("Shivani", "Kaash humaare baaki university friends bhi yahaan aa sakte!"),
            ("You", "Sahi baat hai yaar! Agar vo sab yahaan hote, toh poora improv troupe recreate ho jaataa.")
        ],
        "quiz_concepts": [
            ("'Kyaa hum chalenge?' aur 'Kyaa hum chalein?' mein tone kaa kyaa difference hai?",
             "**Answer:** *'Kyaa hum chalenge?'* future tense mein factual inquiry hai (\"Will we be going?\"), jabki *'Kyaa hum chalein?'* subjunctive mood mein polite, collaborative invitation hai (\"Shall we head out now?\")."),
            ("'Kaash' clauses mein verb ka kaun sa aspect use hota hai?",
             "**Answer:** *Kaash* clauses mein tense auxiliary (*thaa/thee*) drop ho jaati hai aur verb bare habitual participle (*-taa, -tee, -te*) par end hotii hai (*Kaash main vahaan hotaa*).")
        ],
        "quiz_translations": [
            ("Shall I book our return train tickets now? (informal, m)",
             "`Kyaa main abhi humaari return train tickets book karoon?` — क्या मैं अभी हमारी रिटर्न ट्रेन टिकट्स बुक करूँ?",
             "[Kyaa main + abhi (now) + humaari return train tickets + book karoon (shall I book [subjunctive])?]."),
            ("I wish I had more free time for piano practice this month. (informal, m)",
             "`Kaash is maheene mere paas piano practice ke liye thodaa aur time hotaa.` — काश इस महीने मेरे पास पियानो प्रैक्टिस के लिए थोड़ा और टाइम होता।",
             "[Kaash + is maheene (this month) + mere paas + piano practice ke liye + thodaa aur time hotaa]."),
            ("If you lived in Toronto, we would attend live improv shows together. (casual)",
             "`Agar tum Toronto mein rahtii, toh hum saath mein live improv shows dekhne jaate.` — अगर तुम टोरंटो में रहती, तो हम साथ में लाइव इम्प्रोव शोज़ देखने जाते।",
             "[Agar tum Toronto mein rahtii + toh hum saath mein + live improv shows dekhne jaate]."),
            ("Should we wait for ten minutes or leave right away? (polite)",
             "`Kyaa hum das minutes wait karein ya abhi nikal chalein?` — क्या हम दस मिनट्स वेट करें या अभी निकल चलें?",
             "[Kyaa hum das minutes wait karein + ya abhi nikal chalein?]."),
            ("May you always succeed in your new career path! (blessing/wish)",
             "`Aap apne naye career path mein hamesha successful hon!` — आप अपने नए करियर पाथ में हमेशा सक्सेसफुल हों!",
             "[Aap apne naye career path mein + hamesha successful hon!].")
        ]
    },

    {
        "code": "A2-08",
        "title": "Lesson A2-08: Core Emotional Descriptors, Mental States & Relational Nuances 🏷️ (Vocabulary Anchor 3)",
        "level": "A2",
        "summary": "Level A2 ke is aakhiri Vocabulary Anchor milestone mein hum deep emotional vocabulary, mental states, aur high-frequency conversational adverbs (*Pareshaan, Hairaan, Shaant, Aamtaur par, Achaanak*) master karenge.",
        "polyglot": [
            ("Perso-Arabic Emotional Loanwords:", "Hindi emotional descriptors jaise *Pareshaan, Hairaan, Shaant, Zaroori* Urdu/Perso-Arabic origin ke hain jo formal aur casual dono registers mein high status rakhte hain."),
            ("Tamil Emotional State Markers:", "Tamil *kavalai/sandhosham* structures ki tarah Hindi adjectives emotional states qualify karte hain.")
        ],
        "formulas": [
            r"\text{Subject} + \text{State Adjective} + \text{Honaa / Rahnaa} \quad (\text{Main khush hoon, vo pareshaan thaa})",
            r"\text{Adverb of Manner/Time} + \text{Clause} \quad (\text{Aamtaur par, Achaanak, Bilkul})"
        ],
        "sections": [
            {
                "title": "🧠 1. Psychological & Emotional States",
                "content": [
                    "* **Pareshaan** (Worried / Troubled): *Workload ki wajah se thodaa pareshaan thaa.*",
                    "* **Hairaan** (Surprised / Shocked): *Shivani ka career pivot dekhkar sab hairaan the.*",
                    "* **Shaant** (Calm / Peaceful): *Norwich kaa atmosphere kaafi shaant hai.*",
                    "* **Khush** (Happy) vs **Udaas** (Sad / Melancholy)"
                ]
            },
            {
                "title": "🎭 2. Situational Descriptors",
                "content": [
                    "* **Ajeeb** (Weird / Strange / Peculiar): *Yeh bohot ajeeb coincidence thaa!*",
                    "* **Zaroori** (Important / Essential): *Fluency ke liye regular practice bohot zaroori hai.*",
                    "* **Khaas** (Special / Unique): *Aaj humaare liye bohot khaas din hai.*"
                ]
            },
            {
                "title": "⚡ 3. High-Frequency Spoken Discourse Adverbs",
                "content": [
                    "* **Aamtaur par** (Usually / In general): *Aamtaur par main weekends par code nahin kartaa.*",
                    "* **Achaanak** (Suddenly / Unexpectedly): *Achaanak baarish shuru ho gayii.*",
                    "* **Bilkul** (Absolutely / Completely): *Aapka point bilkul sahi hai.*",
                    "* **Khaaskar** (Especially / In particular): *Khaaskar evening ke time yahaan bheed hotii hai.*"
                ]
            }
        ],
        "dialogue": [
            ("Shivani", "Pehle jab maine Ford chhodne kaa sochaa, toh main kaafi pareshaan aur confused thee."),
            ("You", "Natural hai yaar. Itnaa badaa change dekhkar log hairaan bhi hote hain. Lekin ab tum kitnii khush aur shaant lag rahii ho!"),
            ("Shivani", "Bilkul! Aamtaur par log career risk lene se darte hain, par yeh step mere liye bohot khaas saabit huaa."),
            ("You", "Sahi baat hai. Mental satisfaction kisi bhi title se zyaadaa zaroori hai.")
        ],
        "quiz_concepts": [
            ("'Aamtaur par' aur 'Achaanak' conversation mein kis type ke transition markers serve karte hain?",
             "**Answer:** *Aamtaur par* routine ya standard habitual behavior describe karta hai (\"Generally / Usually\"), jabki *Achaanak* unexpected change of state ya narrative surprise introduce karta hai (\"Suddenly / Out of the blue\")."),
            ("'Pareshaan' aur 'Udaas' ke internal feeling context mein kyaa nuance hai?",
             "**Answer:** *Pareshaan* stress, anxiety, ya mental tension denote karta hai (\"worried/harried\"), jabki *Udaas* sadness, low spirits, ya sorrow denote karta hai (\"sad/depressed\").")
        ],
        "quiz_translations": [
            ("I was a bit worried about my flight connection, but everything went smoothly. (informal, m)",
             "`Main apnii flight connection ke baare mein thodaa pareshaan thaa, lekin sab smoothly ho gayaa.` — मैं अपनी फ़्लाइट कनेक्शन के बारे में थोड़ा परेशान था, लेकिन सब स्मूथली हो गया।",
             "[Main apnii flight connection ke baare mein + thodaa pareshaan thaa + lekin sab smoothly ho gayaa]."),
            ("Usually, I practice guitar on Sunday afternoons. (informal, m)",
             "`Aamtaur par main Sunday afternoon ko guitar practice kartaa hoon.` — आमतौर पर मैं संडे आफ़्टरनून को गिटार प्रैक्टिस करता हूँ।",
             "[Aamtaur par (usually) + main Sunday afternoon ko + guitar practice kartaa hoon]."),
            ("Suddenly, the train came to a stop in the middle of the countryside. (general)",
             "`Achaanak countryside ke beech mein train ruk gayii.` — अचानक कंट्रीसाइड के बीच में ट्रेन रुक गई।",
             "[Achaanak (suddenly) + countryside ke beech mein + train ruk gayii]."),
            ("Her improv timing is absolutely fantastic, especially in fast comedy games. (informal)",
             "`Unkii improv timing bilkul fantastic hai, khaaskar fast comedy games mein.` — उनकी इम्प्रोव टाइमिंग बिल्कुल फैंटास्टिक है, खासकर फ़ास्ट कॉमेडी गेम्स में।",
             "[Unkii improv timing + bilkul fantastic hai + khaaskar (especially) + fast comedy games mein]."),
            ("It is very important to stay calm during high-pressure work deadlines. (general)",
             "`High-pressure work deadlines ke dauraan shaant rahnaa bohot zaroori hai.` — हाई-प्रेशर वर्क डेडलाइन्स के दौरान शांत रहना बहुत जरूरी है।",
             "[High-pressure work deadlines ke dauraan + shaant rahnaa + bohot zaroori hai].")
        ]
    },

    # --- LEVEL B1 ---
    {
        "code": "B1-01",
        "title": "Lesson B1-01: The Passive Voice & Impersonal Constructions",
        "level": "B1",
        "summary": "Swagat hai Level B1 ke pehle milestone par! Spoken Hindi mein Passive Voice sirf formal news ke liye nahin hotaa, balki daily office updates (*'Meeting cancel kii gayii'*) aur physical incapacity (*'Mujhse wait nahin kiyaa jaataa'*) express karne ka universal tool hai.",
        "polyglot": [
            ("Romance Passive vs Reflexive:", "French (*Ça se fait*) aur Spanish (*Se canceló la reunión*) passive constructions Hindi ke *'Aisaa kiyaa jaataa hai'* aur *'Cancel kiyaa gayaa'* se identical hain."),
            ("Tamil Impersonal Negatives:", "Tamil *-a mudiyaadhu* (jaise *Ennaala kaathirukka mudiyaadhu*) Hindi ke *'Mujhse intezaar nahin kiyaa jaataa'* ke exact dative/instrumental match hai.")
        ],
        "formulas": [
            r"\text{Completed Past Passive}: \text{Past Participle} + \text{Jaanaa (past inflected)} \quad (\text{kiyaa gayaa, bhejaa gayaa})",
            r"\text{Habitual / General Passive}: \text{Past Participle} + \text{Jaataa hai / Jaatii hai} \quad (\text{likhaa jaataa hai})",
            r"\text{Impersonal Incapacity}: \text{Subject} + \text{se} + \text{Verb Stem} + \text{nahin jaataa} \quad (\text{mujhse saha nahin jaataa})"
        ],
        "sections": [
            {
                "title": "💼 1. Completed Passive Actions in Tech & Work",
                "content": [
                    "* *Email bhej dii gayii hai.* (The email has been dispatched.)",
                    "* *Code review complete kiyaa gayaa.* (The code review was completed.)",
                    "* *Tickets book kar liye gaye.* (The tickets have been booked.)"
                ]
            },
            {
                "title": "🏛️ 2. General Rules & Conventional Practices",
                "content": [
                    "* *Yahaan parking allow nahin kii jaatii.* (Parking is not permitted here.)",
                    "* *Improv mein 'Yes, and' rule follow kiyaa jaataa hai.*",
                    "* *Aisaa kyun kahaa jaataa hai?* (Why is it said like this?)"
                ]
            },
            {
                "title": "😫 3. Impersonal Incapacity (Inability / Overwhelmed)",
                "content": [
                    "Jab insaan physically ya mentally kisi cheez ko tolerate ya perform nahin kar paataa:",
                    "* *Mujhse itnaa wait nahin kiyaa jaataa.* (I simply can't bear waiting this long!)",
                    "* *Mujhse itnii thand bardaasht nahin hotii.*",
                    "* *Usse chalaa nahin jaataa.* (He/she is unable to walk.)"
                ]
            }
        ],
        "dialogue": [
            ("Shivani", "Maine sunaa ki tumhaare office mein kuch team restructure kiyaa gayaa?"),
            ("You", "Haan, do naye AI projects launch kiye gaye hain, isliye tasks redistribute kiye gaye."),
            ("Shivani", "Arre baap re! Mujhse itnaa frequent change handle nahin hotaa!"),
            ("You", "Haha, sahi baat hai, par jab sab automate kiyaa jaataa hai, toh pressure kam ho jaataa hai.")
        ],
        "quiz_concepts": [
            ("Active voice 'Maine email bheji' aur Passive voice 'Email bhej dii gayii' mein focus aur subject marker mein kyaa farq hai?",
             "**Answer:** Active mein subject *Maine* agent hai aur focus sender par hai; Passive mein agent background ho jaata hai aur target noun *Email* subject position mein aakar verb agreement control karta hai (*gayii*)."),
            ("'Mujhse spicy food nahin khaayaa jaataa' structure kyaa communicate kartaa hai?",
             "**Answer:** Yeh conscious choice ya refusal nahin, balki physical / involuntary incapacity express karta hai (\"I cannot tolerate / handle eating spicy food\").")
        ],
        "quiz_translations": [
            ("The project documentation has already been updated. (formal/work)",
             "`Project documentation pehle hi update kar dii gayii hai.` — प्रोजेक्ट डॉक्यूमेंटेशन पहले ही अपडेट कर दी गई है।",
             "[Project documentation + pehle hi + update kar dii gayii hai]."),
            ("I can't bear sitting in front of a screen for ten hours straight. (informal, m)",
             "`Mujhse continuous das ghante screen ke saamne nahin baithaa jaataa.` — मुझसे कंटीन्यूअस दस घंटे स्क्रीन के सामने नहीं बैठा जाता।",
             "[Mujhse + continuous das ghante + screen ke saamne + nahin baithaa jaataa]."),
            ("Why was the meeting postponed at the last moment? (polite)",
             "`Aakhiri moment par meeting postpone kyun kii gayii?` — आखिरी मोमेंट पर मीटिंग पोस्टपोन क्यों की गई?",
             "[Aakhiri moment par + meeting + postpone kyun kii gayii?]."),
            ("In Norwich, local heritage is very carefully preserved. (general)",
             "`Norwich mein local heritage bohot dhyan se preserve kiyaa jaataa hai.` — नॉर्विच में लोकल हेरिटेज बहुत ध्यान से प्रिजर्व किया जाता है।",
             "[Norwich mein + local heritage + bohot dhyan se + preserve kiyaa jaataa hai]."),
            ("These tickets were reserved two weeks in advance. (informal)",
             "`Yeh tickets do hafte pehle hi reserve kar liye gaye the.` — यह टिकट्स दो हफ्ते पहले ही रिज़र्व कर लिए गए थे।",
             "[Yeh tickets + do hafte pehle hi + reserve kar liye gaye the].")
        ]
    },

    {
        "code": "B1-02",
        "title": "Lesson B1-02: Causative Verbs & Secondary Agency (Karnaa → Karaanaa → Karvaanaa)",
        "level": "B1",
        "summary": "Jab aap koi kaam khud karne ke bajaay kisi se 'karwaate' hain ya kisi doosre person ko inspire/facilitate karte hain, toh Hindi ki unique **Causative Verb Morphology** active hoti hai. In triples ko master karna higher-level conversational fluency unlock karta hai.",
        "polyglot": [
            ("Tamil Causative System:", "Tamil causatives (*sei -> seivikkai, saapidu -> oottu*) Hindi causative stems (*-aa-* aur *-vaa-*) ke exact equivalent hain."),
            ("Romance 'Faire faire' Structure:", "French (*faire faire / faire manger*) aur Spanish (*hacer hacer*) direct Hindi *karaanaa / karvaanaa* se map hote hain.")
        ],
        "formulas": [
            r"\text{Base Verb} \longrightarrow \text{1st Causative (-aa-)} \longrightarrow \text{2nd Causative (-vaa-)}",
            r"\text{Karnaa} \longrightarrow \text{Karaanaa} \longrightarrow \text{Karvaanaa} \quad (\text{do} \to \text{have done})",
            r"\text{Intermediary Agent}: \text{Person} + \text{se} \quad (\text{Maine Shivani se baat karvaayii})"
        ],
        "sections": [
            {
                "title": "🔄 1. High-Frequency Causative Triples",
                "content": [
                    "* **Karnaa** (To do) $\\to$ **Karaanaa** $\\to$ **Karvaanaa**: *Maine laptop repair karvaayaa.*",
                    "* **Khaanaa** (To eat) $\\to$ **Khilaanaa** (To feed / treat): *Shivani ko dinner khilaaoongaa.*",
                    "* **Peenaa** (To drink) $\\to$ **Pilaanaa** (To serve drinks): *Pub mein ek round pilaaoongaa.*",
                    "* **Dekhnaa** (To see) $\\to$ **Dikhanaaa** (To show): *Norwich photos dikhaanaa!*",
                    "* **Milnaa** (To meet) $\\to$ **Milaanaa** (To introduce): *Main Shivani ko apne doston se milaaoongaa.*"
                ]
            },
            {
                "title": "🤝 2. Secondary Agency & The 'Se' Connector",
                "content": [
                    "Jab aap kisi intermediary ke through kaam karwate hain:",
                    "* *Maine mechanic se car service karvaayii.* (I had the mechanic service the car.)",
                    "* *Maine agent se train tickets book karvaaye.*"
                ]
            }
        ],
        "dialogue": [
            ("Shivani", "Jab tum UK aaoge, toh main tumhe Norwich ke best spots dikhaaoongii aur local food khilaaoongii!"),
            ("You", "Awesome! Aur pub mein main sabko ek round drinks pilaaoongaa."),
            ("Shivani", "Haha deal! Aur main tumhe apne care home team ke kuch logon se bhi milaaoongii."),
            ("You", "Great! Mujhe unse milkar unke experiences sunne mein bohot interest hogaa.")
        ],
        "quiz_concepts": [
            ("First Causative (e.g. *Khilaanaa*) aur Second Causative (e.g. *Khilvaanaa*) mein kyaa functional difference hotaa hai?",
             "**Answer:** First causative mein subject directly doosre ko action perform karwaata hai (*Maine bacche ko khilaayaa* = I fed the child); Second causative mein subject kisi teesre person (intermediary) se action execute karwaata hai (*Maine Shivani se usko khilvaayaa*)."),
            ("Causative sentences mein intermediary agent (the person who actually does the physical work) kaun sa postposition leta hai?",
             "**Answer:** Intermediary agent postposition **Se** leta hai (*Maine developer se code review karvaayaa*).")
        ],
        "quiz_translations": [
            ("I got my acoustic guitar tuned and serviced at the local music shop. (informal, m)",
             "`Maine local music shop par apna acoustic guitar tune aur service karvaayaa.` — मैंने लोकल म्यूजिक शॉप पर अपना अकूस्टिक गिटार ट्यून और सर्विस करवाया।",
             "[Maine + local music shop par + apna acoustic guitar + tune aur service karvaayaa]."),
            ("Please show me the new photos of your Norwich apartment. (polite)",
             "`Kripya mujhe apne Norwich apartment ki nayi photos dikhaaiye.` — कृपया मुझे अपने नॉर्विच अपार्टमेंट की नई फ़ोटोज़ दिखाइए।",
             "[Kripya mujhe + apne Norwich apartment ki nayi photos + dikhaaiye (please show)]."),
            ("I will introduce you to my AI tech colleagues in Toronto. (casual, m)",
             "`Main tumhe Toronto mein apne AI tech colleagues se milaaoongaa.` — मैं तुम्हें टोरंटो में अपने AI टेक कलीग्स से मिलाऊँगा।",
             "[Main tumhe + Toronto mein + apne AI tech colleagues se + milaaoongaa (will introduce)]."),
            ("Can you please have the cab driver stop near the station entrance? (polite)",
             "`Kyaa aap cab driver se gaadi station entrance ke paas rukvaa sakte hain?` — क्या आप कैब ड्राइवर से गाड़ी स्टेशन एंट्रेंस के पास रुकवा सकते हैं?",
             "[Kyaa aap + cab driver se + gaadi + station entrance ke paas + rukvaa sakte hain?]."),
            ("She treated everyone to delicious homemade chai after the rehearsal. (informal)",
             "`Rehearsal ke baad unhone sabko delicious homemade chaay pilaayii.` — रिहर्सल के बाद उन्होंने सबको डिलीशियस होममेड चाय पिलाई।",
             "[Rehearsal ke baad + unhone sabko + delicious homemade chaay + pilaayii (served drinks)].")
        ]
    },

    {
        "code": "B1-03",
        "title": "Lesson B1-03: High-Yield Abstract Concepts, Trust & Relational Vocabulary 🏷️ (Vocabulary Anchor 4)",
        "level": "B1",
        "summary": "Deep friendship catch-ups, philosophical banter, aur professional reflections mein abstract vocabulary ki zaroorat padtii hai. Is lesson mein hum trust (*Bharosaa*), decision (*Faislaa*), responsibility (*Zimmedaari*), aur value (*Farq, Faaydaa*) master karenge.",
        "polyglot": [
            ("Perso-Arabic Relational Nuances:", "Hindi words *Bharosaa, Faislaa, Zimmedaari, Ehsaas, Haq* Urdu aur Persian heritage ke hain jo intellectual debates aur emotional warmth dono deliver karte hain."),
            ("Tamil Abstract Noun Parallels:", "Tamil *nambikkai* (trust) -> *Bharosaa*, *mudivu* (decision) -> *Faislaa*, *poruppu* (responsibility) -> *Zimmedaari* ke exact philosophical equivalents hain.")
        ],
        "formulas": [
            r"\text{Trust on someone}: \text{Kisi par} + \text{Bharosaa / Vishwaas karnaa}",
            r"\text{Difference / Impact}: \text{Isse} + \text{koi farq nahin padtaa} \quad (\text{It makes no difference})",
            r"\text{Taking a decision}: \text{Faislaa karnaa / Lenaa}"
        ],
        "sections": [
            {
                "title": "🤝 1. Trust, Faith & Truth",
                "content": [
                    "* **Bharosaa / Vishwaas:** *Mujhe Shivani par poora bharosaa hai.* (I trust Shivani completely.)",
                    "* **Umeed:** *Humein achhe weather ki umeed hai.* (We have hope/expectation of good weather.)",
                    "* **Sachchaai:** *Sachchaai hamesha samne aatii hai.* (The truth always emerges.)"
                ]
            },
            {
                "title": "⚖️ 2. Agency, Decisions & Responsibility",
                "content": [
                    "* **Faislaa:** *Engineering se care home pivot karna ek bold faislaa thaa.*",
                    "* **Zimmedaari:** *Yeh meri personal zimmedaari hai.* (This is my responsibility.)",
                    "* **Koshish:** *Hum har situation mein best koshish karte hain.* (Effort / Attempt)",
                    "* **Haq:** *Har kisi ko apnii baat kehne kaa haq hai.* (Right / Entitlement)"
                ]
            },
            {
                "title": "🌱 3. Social Bonds & Outcomes",
                "content": [
                    "* **Rishtaa & Dosti:** *Purani dosti hamesha strong rahtii hai.*",
                    "* **Ehsaas:** *Yeh ehsaas bohot comforting hai.* (This realization/feeling)",
                    "* **Faaydaa vs Nuqsaan:** *Is approach kaa kyaa faaydaa hai?*",
                    "* **Farq:** *Isse koi farq nahin padtaa.* (It doesn't make any difference.)"
                ]
            }
        ],
        "dialogue": [
            ("Shivani", "Jab maine job change kaa faislaa liyaa, toh shuru mein bohot risk lagaa. Par mujhe apne instinct par bharosaa thaa."),
            ("You", "Bilkul sahi kiyaa! Career mein satisfaction zyaadaa zaroori hai. Jab hum try hi na karein toh faaydaa kyaa?"),
            ("Shivani", "Sahi baat hai! Jab tak aap responsibility lekar move nahin karte, tab tak change kaa ehsaas nahin hotaa."),
            ("You", "Aur sachchi dosti ki beauty yahi hai ki time ya distance se koi farq nahin padtaa.")
        ],
        "quiz_concepts": [
            ("'Kisi par bharosaa karnaa' mein preposition/postposition kaun sa lagtaa hai?",
             "**Answer:** Postposition **Par** lagtaa hai (*Mujhe aap par bharosaa hai* = I trust in you / upon you)."),
            ("'Isse koi farq nahin padtaa' phrase spoken Hindi mein kis context mein use hota hai?",
             "**Answer:** Yeh reassurance ya indifference express karne ke liye use hota hai (\"It doesn't make any difference / It doesn't matter at all\").")
        ],
        "quiz_translations": [
            ("I have complete trust in your judgment and improv instincts. (casual, to Shivani)",
             "`Mujhe tumhaare judgment aur improv instincts par poora bharosaa hai.` — मुझे तुम्हारे जजमेंट और इम्प्रोव इंस्टिंक्ट्स पर पूरा भरोसा है।",
             "[Mujhe + tumhaare judgment aur improv instincts par + poora bharosaa hai]."),
            ("Taking full responsibility for one's life decisions brings true freedom. (general)",
             "`Apne life decisions ki poori zimmedaari lene se sachchi freedom miltii hai.` — अपने लाइफ डिसीजन्स की पूरी ज़िम्मेदारी लेने से सच्ची फ़्रीडम मिलती है।",
             "[Apne life decisions ki poori zimmedaari lene se + sachchi freedom miltii hai]."),
            ("It makes no difference whether we take the afternoon or evening train. (informal)",
             "`Isse koi farq nahin padtaa ki hum afternoon train lein ya evening train.` — इससे कोई फ़र्क नहीं पड़ता कि हम आफ़्टरनून ट्रेन लें या इवनिंग ट्रेन।",
             "[Isse koi farq nahin padtaa + ki hum afternoon train lein ya evening train]."),
            ("We should make every effort to reach the reunion dinner on time. (polite)",
             "`Humein reunion dinner par time se pahunchne ki poori koshish karnii chaahiye.` — हमें रीयूनियन डिनर पर टाइम से पहुँचने की पूरी कोशिश करनी चाहिए।",
             "[Humein + reunion dinner par time se pahunchne ki + poori koshish karnii chaahiye]."),
            ("Distance makes no impact on authentic long-term friendships. (general)",
             "`Distance se sachchi long-term dosti par koi farq nahin padtaa.` — डिस्टेंस से सच्ची लॉन्ग-टर्म दोस्ती पर कोई फ़र्क नहीं पड़ता।",
             "[Distance se + sachchi long-term dosti par + koi farq nahin padtaa].")
        ]
    },

    {
        "code": "B1-04",
        "title": "Lesson B1-04: Adverbial Participles & Complex Clause Modifiers",
        "level": "B1",
        "summary": "Complex, natural narrative fluency ke liye Adverbial Participles (*-te hue, -kar / -karke, -te hi*) Hindi ka ultimate syntactic engine hain. Inke zariye aap simultaneous actions, sequential steps, aur instantaneous triggers ko bina cumbersome conjunctions ke compactly link kar sakte hain.",
        "polyglot": [
            ("Tamil Adverbial Participle Mirror:", "Tamil adverbial participles (*-kittu* for simultaneous: *pesikitte*, *-adhuve* for immediate: *vandhadhum*, verbal participle *-thu* for sequential: *saaptu*) Hindi participles ke 100% exact syntactic parallels hain."),
            ("Romance Gerunds:", "French (*en buvant du café*) aur Spanish (*hablando / habiendo comido*) exact *-te hue* aur *-kar* clauses se match karte hain.")
        ],
        "formulas": [
            r"\text{Simultaneous Action}: \text{Verb Stem} + \text{te hue} \quad (\text{coffee peete hue baat karnaa})",
            r"\text{Sequential Action (Having done X)}: \text{Verb Stem} + \text{kar / karke} \quad (\text{khaanaa khaakar nikalnaa})",
            r"\text{Immediate Trigger (As soon as)}: \text{Verb Stem} + \text{te hi} \quad (\text{pahunchte hi call karnaa})"
        ],
        "sections": [
            {
                "title": "☕ 1. Imperfective Participles (-te hue: Simultaneous)",
                "content": [
                    "Jab do actions ek hi time par simultaneously ho rahe hon:",
                    "* *Hum coffee peete hue purani university memories discuss karenge.*",
                    "* *Chalte-chalte maine yeh observation notice kiyaa.* (While walking along...)",
                    "* *Music sunte hue coding karna bohot relaxing hotaa hai.*"
                ]
            },
            {
                "title": "🏁 2. Perfective Participles (-kar / -karke: Sequential)",
                "content": [
                    "Jab pehla action successfully finish ho kar agla action trigger hota hai ('Having done X, then Y'):",
                    "* *Khaanaa khaakar hum river walk par chalenge.*",
                    "* *Soch-samajhkar koi bhi response choose karo.*",
                    "* *Files save karke laptop shut down kar do.*"
                ]
            },
            {
                "title": "⚡ 3. Immediate Sequence (-te hi: Instantaneous)",
                "content": [
                    "Jab ek action ke hote hi doosra action instantly trigger hota hai ('As soon as'):",
                    "* *Norwich station pahunchte hi mujhe message kar denaa.*",
                    "* *Alarm bajte hi main uth gayaa.*",
                    "* *Meeting end hote hi feedback share karenge.*"
                ]
            }
        ],
        "dialogue": [
            ("Shivani", "Station pahunchte hi mujhe call kar denaa, main station ke bahar wait kar rahii hoongii!"),
            ("You", "Bilkul! Train se utarte hi phone karoongaa. Phir cafe mein baithkar coffee peete hue aaraam se catch-up karenge."),
            ("Shivani", "Awesome plan! Phir evening mein khaanaa khaakar pub chalenge.")
        ],
        "quiz_concepts": [
            ("'-te hue' aur '-kar' clauses mein temporal sequence kaa kyaa fundamental farq hai?",
             "**Answer:** *-te hue* simultaneous ongoing actions show karta hai jo parallel chal rahe hain (*TV dekhte hue khaanaa*), jabki *-kar / -karke* sequential action show karta hai jisme pehla action complete hone ke baad agla action start hota hai (*Khaanaa khaakar nikalnaa*)."),
            ("'Pahunchte hi mujhe call karnaa' mein '-te hi' particle kyaa convey karta hai?",
             "**Answer:** Yeh zero time delay ya instantaneous sequence convey karta hai (\"As soon as you arrive, call me\").")
        ],
        "quiz_translations": [
            ("We will discuss our travel plans while drinking coffee in the cafe. (informal, m)",
             "`Hum cafe mein coffee peete hue apne travel plans discuss karenge.` — हम कैफ़े में कॉफ़ी पीते हुए अपने ट्रेवल प्लान्स डिस्कस करेंगे।",
             "[Hum cafe mein + coffee peete hue (while drinking coffee) + apne travel plans discuss karenge]."),
            ("As soon as the flight landed, I texted my friends in Toronto. (informal, m)",
             "`Flight land hote hi maine Toronto mein apne doston ko text kiyaa.` — फ़्लाइट लैंड होते ही मैंने टोरंटो में अपने दोस्तों को टेक्स्ट किया।",
             "[Flight land hote hi (as soon as flight landed) + maine Toronto mein apne doston ko text kiyaa]."),
            ("After finishing work, let's go for a walk along the river. (casual)",
             "`Kaam khatam karke, river ke kinaare walk par chalte hain.` — काम खत्म करके, रिवर के किनारे वॉक पर चलते हैं।",
             "[Kaam khatam karke (after finishing work) + river ke kinaare walk par chalte hain]."),
            ("Think carefully before making any major career transition. (polite)",
             "`Koi bhi badaa career transition karne se pehle achhe se soch-samajhkar faislaa kijiye.` — कोई भी बड़ा करियर ट्रांज़िशन करने से पहले अच्छे से सोच-समझकर फ़ैसला कीजिए।",
             "[Koi bhi badaa career transition karne se pehle + achhe se soch-samajhkar (having thought carefully) + faislaa kijiye]."),
            ("While listening to acoustic guitar melodies, I feel completely relaxed. (informal, m)",
             "`Acoustic guitar melodies sunte hue, main bilkul relaxed feel kartaa hoon.` — अकूस्टिक गिटार मेलोडीज़ सुनते हुए, मैं बिल्कुल रिलैक्स्ड फील करता हूँ।",
             "[Acoustic guitar melodies sunte hue + main bilkul relaxed feel kartaa hoon].")
        ]
    },

    {
        "code": "B1-05",
        "title": "Lesson B1-05: Conversational Idioms, Expressive Phrasal Formulas & Colloquial Discourse 🏷️ (Vocabulary Anchor 5)",
        "level": "B1",
        "summary": "Authentic conversational naturalness idioms aur colloquial phrasal formulas se aatii hai. Is milestone mein hum street-smart inquiries (*'Chakkar kyaa hai?'*), intention markers (*Jaan-bujhkar, Galti se, Aise hi*), aur popular Hinglish metaphors (*Taang kheenchnaa, Dimag kharaab karnaa*) master karenge.",
        "polyglot": [
            ("Metaphorical Idiom Alignments:", "English 'pulling someone's leg' directly corresponds to Hindi *'Taang kheenchnaa'*, aur French 'avoir la tête comme une citrouille' corresponds to *'Dimag kharaab hona'*."),
            ("Tamil Colloquial Fillers:", "Tamil *Summaa* (just like that / casually) exact twin hai Hindi *'Aise hi'* kaa.")
        ],
        "formulas": [
            r"\text{Street Inquiry}: \text{Chakkar kyaa hai?} \quad (\text{What's the catch / deal?})",
            r"\text{Intentionality}: \text{Jaan-bujhkar (deliberately)}, \text{Galti se (by accident)}, \text{Aise hi (casually)}",
            r"\text{Discourse Pivots}: \text{Khair (anyway)}, \text{Darasal (as a matter of fact)}, \text{Dekhaa jaaye toh (if you look at it)}"
        ],
        "sections": [
            {
                "title": "🕵️ 1. Inquiries & Nuance Markers",
                "content": [
                    "* **Chakkar kyaa hai?** (What is the real catch / situation?): *Itnii jaldi plan change huaa, chakkar kyaa hai?*",
                    "* **Kise pataa?** (Who knows? / Who can tell?): *Future mein kyaa hogaa, kise pataa!*",
                    "* **Jaan-bujhkar** vs **Galti se**: *Maine jaan-bujhkar nahin kiyaa, galti se ho gayaa.*",
                    "* **Aise hi:** *Main aise hi puch rahaa thaa.* (I was just asking casually.)"
                ]
            },
            {
                "title": "🔀 2. Conversational Pivots",
                "content": [
                    "* **Khair:** *Khair, chhoro yeh sab, main topics par aate hain.* (Anyway, let that be...)",
                    "* **Darasal:** *Darasal, baat yeh hai ki train delay ho gayii.* (Actually, the matter is...)",
                    "* **Dekhaa jaaye toh:** *Dekhaa jaaye toh, dono options ke apne benefits hain.*"
                ]
            },
            {
                "title": "🎭 3. Popular Spoken Metaphors",
                "content": [
                    "* **Taang kheenchnaa:** *Fikar mat karo, main bas tumhaari taang kheench rahaa thaa!* (Pulling your leg)",
                    "* **Dimag kharaab karnaa:** *Bug ne mera dimag kharaab kar diyaa.* (The bug drove me nuts.)",
                    "* **Hawaa nikalnaa:** *Lambii walk ke baad meri hawaa nikal gayii.* (Ran out of steam.)"
                ]
            }
        ],
        "dialogue": [
            ("Shivani", "Wait, kyaa tum sach mein airport par apna luggage bhool gaye the?!"),
            ("You", "Haha arre nahin yaar! Main toh bas tumhaari taang kheench rahaa thaa!"),
            ("Shivani", "Oof! Ek second ke liye mera dimag kharaab ho gayaa thaa! Maine sochaa yeh sach thaa."),
            ("You", "Khair, darasal sab kuch perfect thaa. Dekhaa jaaye toh yeh meri sabse smooth international trip rahii.")
        ],
        "quiz_concepts": [
            ("'Jaan-bujhkar' aur 'Galti se' mein legal / moral accountability kaise express hotii hai?",
             "**Answer:** *Jaan-bujhkar* conscious intentionality denote karta hai (\"deliberately/on purpose\"), jabki *Galti se* unintentional error ya accident denote karta hai (\"by mistake/inadvertently\")."),
            ("'Khair' word conversation mein kis time sabse effective serve karta hai?",
             "**Answer:** *Khair* conversation ko tangents ya unnecessary details se wapas core topic par pivot karne ke liye (\"anyway / regardless / moving on\") use hota hai.")
        ],
        "quiz_translations": [
            ("Don't take it seriously, she was just pulling your leg during the improv game! (casual)",
             "`Ise seriously mat lo, vo improv game ke dauraan bas tumhaari taang kheench rahii thee!` — इसे सीरियसली मत लो, वह इम्प्रोव गेम के दौरान बस तुम्हारी टांग खींच रही थी!",
             "[Ise seriously mat lo + vo improv game ke dauraan + bas tumhaari taang kheench rahii thee!]."),
            ("I didn't make this coding error on purpose, it happened by mistake. (informal, m)",
             "`Maine yeh coding error jaan-bujhkar nahin kiyaa, galti se ho gayaa.` — मैंने यह कोडिंग एरर जान-बूझकर नहीं किया, गलती से हो गया।",
             "[Maine yeh coding error jaan-bujhkar nahin kiyaa + galti se ho gayaa]."),
            ("Anyway, as a matter of fact, we have plenty of time before the show starts. (informal)",
             "`Khair, darasal, show shuru hone se pehle humaare paas kaafi time hai.` — खैर, दरअसल, शो शुरू होने से पहले हमारे पास काफ़ी टाइम है।",
             "[Khair + darasal + show shuru hone se pehle + humaare paas kaafi time hai]."),
            ("What's the catch behind this sudden change of plan? (casual)",
             "`Is sudden change of plan ke peeche chakkar kyaa hai?` — इस सडन चेंज ऑफ़ प्लान के पीछे चक्कर क्या है?",
             "[Is sudden change of plan ke peeche + chakkar kyaa hai?]."),
            ("If you look at it objectively, living in Norwich is much calmer than Toronto. (informal, m)",
             "`Dekhaa jaaye toh, Toronto ke comparison mein Norwich mein rahnaa bohot shaant hai.` — देखा जाए तो, टोरंटो के कम्पेरिज़न में नॉर्विच में रहना बहुत शांत है।",
             "[Dekhaa jaaye toh + Toronto ke comparison mein + Norwich mein rahnaa bohot shaant hai].")
        ]
    },

    {
        "code": "B1-06",
        "title": "Lesson B1-06: Presumptive Mood, Deductions & Speculative Future (Hogaa / Kar Rahaa Hogaa)",
        "level": "B1",
        "summary": "Jab aap future action ke baare mein predict karne ke bajaay PRESENT ya PAST situations ke baare mein smart deductions ya speculations lagate hain, toh Hindi ka **Presumptive Mood** (*Hogaa, Kar rahaa hogaa, Liyaa hogaa*) use hota hai. Yeh polyglot discourse ka high-level reasoning tool hai.",
        "polyglot": [
            ("Romance Epistemic Future:", "Spanish (*Estará en la oficina* = He must be in the office right now) aur French (*Il sera déjà parti*) exact presumptive future mechanics follow karte hain."),
            ("English Modal Equivalents:", "English 'must be doing' / 'must have seen' direct Hindi *hogaa* structures se match karte hain.")
        ],
        "formulas": [
            r"\text{Present State Deduction}: \text{Subject} + [\text{Location / State}] + \text{Hogaa / Hogii / Honge}",
            r"\text{Present Continuous Deduction}: \text{Verb Stem} + \text{rahaa hogaa / rahii hogii} \quad (\text{must be doing right now})",
            r"\text{Past Completed Deduction}: \text{Past Participle} + \text{hogaa / hogii} \quad (\text{dekh liyaa hogaa = must have seen})"
        ],
        "sections": [
            {
                "title": "🏢 1. Present State Deductions",
                "content": [
                    "* *Vo abhi office mein hogaa.* (He must be in the office right now.)",
                    "* *Shivani abhi care home mein hogii.* (Shivani must be at the care home right now.)",
                    "* *Pub abhi crowded hogaa.* (The pub must be crowded right now.)"
                ]
            },
            {
                "title": "🚆 2. Ongoing Deductions (Must be doing)",
                "content": [
                    "* *Vo abhi train mein travel kar rahii hogii.* (She must be traveling on the train right now.)",
                    "* *Team abhi code review kar rahii hogii.*",
                    "* *Toronto mein abhi subah ho rahii hogii.* (It must be morning in Toronto right now.)"
                ]
            },
            {
                "title": "📩 3. Past Completed Deductions (Must have done)",
                "content": [
                    "* *Usne mera message dekh liyaa hogaa.* (He/she must have seen my message by now.)",
                    "* *Flight land ho gayii hogii.* (The flight must have landed already.)",
                    "* *Unhone dinner kar liyaa hogaa.*"
                ]
            }
        ],
        "dialogue": [
            ("Shivani", "Maine phone silent par rakh diyaa thaa. Tumne cab book kar lii kyaa?"),
            ("You", "Haan, cab book ho gayii hai. Driver abhi doosre block mein wait kar rahaa hogaa."),
            ("Shivani", "Great! Aur pub mein unhone humaari table reserve kar lii hogii."),
            ("You", "Bilkul! 10 minutes mein pahunchte hain, tab tak drinks prepare ho rahii hongii.")
        ],
        "quiz_concepts": [
            ("'Vo office mein hai' aur 'Vo office mein hogaa' mein reality status kaa kyaa difference hai?",
             "**Answer:** *'Vo office mein hai'* direct factual assertion hai (100% known truth), jabki *'Vo office mein hogaa'* presumptive deduction hai (\"He must be in the office / I deduce he is there based on routine\")."),
            ("Completed past deduction 'Usne dekh liyaa hogaa' mein verb agreement kaun decide karta hai?",
             "**Answer:** Ergative *Ne* rule ke accordance mein, verb object ke gender aur number se agree karti hai (*Usne message [m] dekh liyaa hogaa*, *Usne email [f] dekh lii hogii*).")
        ],
        "quiz_translations": [
            ("She must be preparing for her afternoon shift at the care home right now. (informal)",
             "`Vo abhi care home mein apnii afternoon shift ke liye prepare kar rahii hogii.` — वह अभी केयर होम में अपनी आफ़्टरनून शिफ्ट के लिए प्रिपेयर कर रही होगी।",
             "[Vo abhi + care home mein + apnii afternoon shift ke liye + prepare kar rahii hogii]."),
            ("The AI team in Toronto must have deployed the latest model release by now. (informal)",
             "`Toronto mein AI team ne ab tak latest model release deploy kar diyaa hogaa.` — टोरंटो में AI टीम ने अब तक लेटेस्ट मॉडल रिलीज़ डिप्लॉय कर दिया होगा।",
             "[Toronto mein AI team ne + ab tak (by now) + latest model release + deploy kar diyaa hogaa]."),
            ("It must be raining in Norwich today, take your umbrella along. (casual)",
             "`Aaj Norwich mein baarish ho rahii hogii, apnaa umbrella saath le lo.` — आज नॉर्विच में बारिश हो रही होगी, अपना अम्ब्रेला साथ ले लो।",
             "[Aaj Norwich mein + baarish ho rahii hogii + apnaa umbrella saath le lo]."),
            ("They must have already reserved our riverside table. (polite)",
             "`Unhone pehle hi humaari riverside table reserve kar lii hogii.` — उन्होंने पहले ही हमारी रिवरसाइड टेबल रिज़र्व कर ली होगी।",
             "[Unhone pehle hi + humaari riverside table + reserve kar lii hogii]."),
            ("He must be resting after that long transatlantic flight. (informal, m)",
             "`Vo us lambii transatlantic flight ke baad abhi aaraam kar rahaa hogaa.` — वह उस लंबी ट्रांसअटलांटिक फ़्लाइट के बाद अभी आराम कर रहा होगा।",
             "[Vo us lambii transatlantic flight ke baad + abhi aaraam kar rahaa hogaa].")
        ]
    },

    {
        "code": "B1-07",
        "title": "Lesson B1-07: Comprehensive B1 Synthesis & Spontaneous Conversational Fluency",
        "level": "B1",
        "summary": "Badhaai ho! Aap humaare master B1 curriculum ke supreme summit par pahunch gaye hain: **Comprehensive B1 Synthesis & Spontaneous Conversational Fluency**! Is culmination lesson mein hum passive voice, causatives, participles, correlatives, presumptive reasoning, aur urban Hinglish code-switching ko seamlessly fuse karenge ek complete real-world immersion dialogue mein.",
        "polyglot": [
            ("Full Polyglot Mastery:", "Aapka SOV alignment, dative experiencers, aspectual auxiliaries, aur Romance conjunction parallels ab ek unified instinctual operating system ban chuke hain."),
            ("Target Fluency Benchmark:", "October Norwich reunion mein bina kisi translation delay ke deep catch-ups, professional life pivots, improv comedy banter, aur travel navigation spontenously deliver karna.")
        ],
        "formulas": [
            r"\text{B1 Full Integration}: \text{Participles} + \text{Compound Aspect} + \text{Presumptive} + \text{Hinglish Code-Switching}",
            r"\text{Spontaneous Synthesis}: \text{Bina hesitations ke complex clauses aur opinions express karnaa}"
        ],
        "sections": [
            {
                "title": "👑 1. The Full Synthesis Ecosystem",
                "content": [
                    "B1 fluency ka matlab formal academic sentences bolna nahin hai, balki multiple grammar tools ko naturally thread karna hai:",
                    "* *Participles:* Cafe mein baithkar coffee peete hue...",
                    "* *Compound Verbs:* Maine saare plans confirm kar liye hain...",
                    "* *Causatives:* Main tumhe sabse milwaaoongaa...",
                    "* *Correlatives:* Jahaan achhaa atmosphere hotaa hai, vahaan baatcheet flow kartii hai...",
                    "* *Presumptive:* Vo log abhi aa rahe honge."
                ]
            },
            {
                "title": "🎙️ 2. The Norwich Improv & Life Catch-Up Master Dialogue",
                "content": [
                    "Imagine kijiye: Aap aur Shivani Norwich ke ek classic historic pub mein riverside table par baithe hain:",
                    "Aapki Hindi smooth, witty, confident, aur natural Hinglish nuances se full hai."
                ]
            }
        ],
        "dialogue": [
            ("Shivani", "Sach mein yaar, mujhe vishwaas nahin ho rahaa ki hum UK mein riverside pub par baithe hain! Toronto se Norwich kaa transition kaisaa lagaa?"),
            ("You", "Bilkul dream jaisaa lag rahaa hai! Flight land hote hi maine train pakad lii aur aaraam se yahaan pahunch gayaa. Norwich sach mein bohot shaant aur khoobsoorat shehar hai."),
            ("Shivani", "Sahi baat hai! Aur mera care home lifestyle coordinator kaa role dekhkar pehle sab hairaan the, par ab sabko samajh aa gayaa ki yeh kitnaa fulfilling faislaa thaa."),
            ("You", "Meraa pakkaa maannaa hai ki work-satisfaction kisi bhi traditional title se badaa hotaa hai. Jahaan genuine happiness miltii hai, wahi kaam best hotaa hai."),
            ("Shivani", "Exactly! Aur suno, shaam ko main tumhe apne improv group ke doston se milwaaoongii. Humne ek chhotii comedy jam session plan karvaayii hai!"),
            ("You", "Wah, kamaal hai! Main zaroor participate karoongaa. University ke improv days yaad aa gaye. Chalo, is baat par agla round meri taraf se!")
        ],
        "quiz_concepts": [
            ("Spontaneous spoken fluency mein complex sentences frame karte waqt code-switching ka sabse safe aur natural balance kyaa hotaa hai?",
             "**Answer:** Core nouns aur technical/modern descriptors English mein natural hote hain (*career pivot, improv session, riverside table*), jabki grammatical glue (postpositions *me/se/par*, auxiliaries *kar rahaa hoon, kar diyaa*, participles *-te hue*) 100% Hindi structural frame follow karte hain."),
            ("B1 level achieve karne ke baad Anki flashcard review aur daily conversation maintenance kaa kyaa ongoing formula hona chaahiye?",
             "**Answer:** Regular active recall drills (daily target cards), weekly spontaneous voice journaling, aur Hindi media / lyrics analysis ke through learned patterns ko active memory mein consolidate karte rahnaa.")
        ],
        "quiz_translations": [
            ("Having arrived in Norwich, I feel that this reunion was the best decision of the year. (informal, m)",
             "`Norwich pahunchkar, mujhe lagtaa hai ki yeh reunion saal kaa sabse best faislaa thaa.` — नॉर्विच पहुँचकर, मुझे लगता है कि यह रीयूनियन साल का सबसे बेस्ट फ़ैसला था।",
             "[Norwich pahunchkar (having arrived) + mujhe lagtaa hai (I feel) + ki yeh reunion + saal kaa sabse best faislaa thaa]."),
            ("While sitting in the pub, we reminisced about all our university improv performances. (informal, m)",
             "`Pub mein baithkar, humne apnii saari university improv performances yaad keen.` — पब में बैठकर, हमने अपनी सारी यूनिवर्सिटी इम्प्रोव परफ़ॉर्मान्सेस याद कीं।",
             "[Pub mein baithkar + humne apnii saari university improv performances + yaad keen]."),
            ("I will introduce Shivani to my tech colleagues as soon as they reach the event. (informal, m)",
             "`Jaise hi tech colleagues event par pahunchenge, main Shivani ko unse milwaaoongaa.` — जैसे ही टेक कलीग्स इवेंट पर पहुँचेंगे, मैं शिवानी को उनसे मिलवाऊँगा।",
             "[Jaise hi tech colleagues event par pahunchenge + main Shivani ko unse milwaaoongaa]."),
            ("It must be quite late in Toronto now, so I will send my project update tomorrow morning. (informal, m)",
             "`Toronto mein abhi kaafi late ho gayaa hogaa, isliye main apna project update kal subah bhejūngaa.` — टोरंटो में अभी काफ़ी लेट हो गया होगा, इसलिए मैं अपना प्रोजेक्ट अपडेट कल सुबह भेजूँगा।",
             "[Toronto mein abhi kaafi late ho gayaa hogaa + isliye main apna project update kal subah bhejūngaa]."),
            ("We can overcome any communicative challenge through consistent daily practice. (general)",
             "`Consistent daily practice ke zariye hum kisi bhi conversational challenge ko overcome kar sakte hain.` — कंसिस्टेंट डेली प्रैक्टिस के ज़रिए हम किसी भी कन्वर्सेशनल चैलेंज को ओवरकम कर सकते हैं।",
             "[Consistent daily practice ke zariye + hum kisi bhi conversational challenge ko + overcome kar sakte hain].")
        ]
    }
]

def generate_lesson_json_and_md(spec):
    code = spec["code"]
    title = spec["title"]
    slug = slugify(code, title)
    lesson_id = str(uuid.uuid4())

    sections = []

    # 1. 🌟Summary
    summary_content = [
        {"type": "paragraph", "text": spec["summary"]}
    ]
    sections.append({
        "title": "🌟Summary",
        "type": "heading_1",
        "content": summary_content
    })

    # Polyglot Anchors
    polyglot_content = []
    for anchor_title, anchor_desc in spec.get("polyglot", []):
        polyglot_content.append({"type": "bullet", "text": f"**{anchor_title}**", "children": []})
        polyglot_content.append({"type": "paragraph", "text": anchor_desc})
    if polyglot_content:
        sections.append({
            "title": "🧠 Polyglot Structural Anchors",
            "type": "heading_3",
            "content": polyglot_content
        })

    # Mathematical Formulas
    formulas_content = []
    for f in spec.get("formulas", []):
        formulas_content.append({"type": "paragraph", "text": f"$${f}$$"})
    if formulas_content:
        sections.append({
            "title": "📐 Core Mathematical Formulas",
            "type": "heading_3",
            "content": formulas_content
        })

    # 2. 📘Lesson
    lesson_root = {
        "title": "📘Lesson",
        "type": "heading_1",
        "content": []
    }
    sections.append(lesson_root)

    for sec in spec.get("sections", []):
        sec_content = []
        for line in sec.get("content", []):
            sec_content.append({"type": "paragraph", "text": line})
        sections.append({
            "title": sec["title"],
            "type": "heading_2",
            "content": sec_content
        })

    # Dialogue
    if spec.get("dialogue"):
        dialogue_content = []
        for spk, text in spec["dialogue"]:
            dialogue_content.append({
                "type": "paragraph",
                "text": f"**{spk}:** *\"{text}\"*"
            })
        sections.append({
            "title": "🎭 Dialogue Example",
            "type": "heading_2",
            "content": dialogue_content
        })

    # 3. ❓Quiz
    quiz_root = {
        "title": "❓Quiz",
        "type": "heading_1",
        "content": []
    }
    sections.append(quiz_root)

    # Concept Questions
    concept_content = []
    for q_text, ans_text in spec.get("quiz_concepts", []):
        concept_content.append({
            "type": "numbered",
            "text": f"**{q_text}**",
            "children": [ans_text]
        })
    sections.append({
        "title": "Concept & Grammar Questions",
        "type": "heading_3",
        "content": concept_content
    })

    # Translation Questions
    translation_content = []
    for en_text, ans_text, breakdown in spec.get("quiz_translations", []):
        translation_content.append({
            "type": "numbered",
            "text": f"**{en_text}**",
            "children": [
                f"**Answer:** {ans_text}",
                breakdown
            ]
        })
    sections.append({
        "title": "Translation Questions",
        "type": "heading_3",
        "content": translation_content
    })

    # Build Markdown text
    md_lines = [
        f"# {title}",
        "",
        "# 🌟Summary",
        "",
        spec["summary"],
        ""
    ]
    if spec.get("polyglot"):
        md_lines.append("### 🧠 Polyglot Structural Anchors\n")
        for anchor_title, anchor_desc in spec["polyglot"]:
            md_lines.append(f"* **{anchor_title}**\n{anchor_desc}\n")

    if spec.get("formulas"):
        md_lines.append("### 📐 Core Mathematical Formulas\n")
        for f in spec["formulas"]:
            md_lines.append(f"$${f}$$\n")

    md_lines.append("---\n")
    md_lines.append("# 📘Lesson\n")

    for sec in spec.get("sections", []):
        md_lines.append(f"## {sec['title']}\n")
        for line in sec.get("content", []):
            md_lines.append(f"{line}\n")

    if spec.get("dialogue"):
        md_lines.append("---\n")
        md_lines.append("## 🎭 Dialogue Example\n")
        for spk, text in spec["dialogue"]:
            md_lines.append(f"* **{spk}:** *\"{text}\"*")
        md_lines.append("")

    md_lines.append("---\n")
    md_lines.append("# ❓Quiz\n")
    md_lines.append("### Concept & Grammar Questions\n")
    for i, (q_text, ans_text) in enumerate(spec.get("quiz_concepts", []), 1):
        md_lines.append(f"1. **{q_text}**")
        md_lines.append(f"    * {ans_text}")
    md_lines.append("\n---\n")

    md_lines.append("### Translation Questions\n")
    for i, (en_text, ans_text, breakdown) in enumerate(spec.get("quiz_translations", []), 1):
        md_lines.append(f"1. **{en_text}**")
        md_lines.append(f"    * **Answer:** {ans_text}")
        md_lines.append(f"    * {breakdown}")

    full_md = "\n".join(md_lines)

    json_data = {
        "id": lesson_id,
        "code": code,
        "title": title,
        "slug": slug,
        "sections": sections,
        "markdown": full_md
    }

    return lesson_id, code, title, slug, json_data, full_md

def main():
    os.makedirs(LESSONS_DIR, exist_ok=True)
    
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        existing_index = json.load(f)

    existing_codes = {item.get('code') for item in existing_index}

    new_entries = []
    for spec in LESSON_SPECS:
        lesson_id, code, title, slug, json_data, full_md = generate_lesson_json_and_md(spec)
        filename_json = f"{slug}.json"
        filename_md = f"{slug}.md"

        # Write JSON
        json_path = os.path.join(LESSONS_DIR, filename_json)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        # Write Markdown
        md_path = os.path.join(LESSONS_DIR, filename_md)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(full_md)

        if code not in existing_codes:
            new_entries.append({
                "id": lesson_id,
                "code": code,
                "title": title,
                "slug": slug,
                "filename": filename_json
            })
            existing_codes.add(code)
            print(f"Generated {code}: {title} -> {filename_json}")
        else:
            print(f"Updated {code}: {title} -> {filename_json}")

    # Combine and save updated index
    updated_index = existing_index + new_entries
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(updated_index, f, ensure_ascii=False, indent=2)

    print(f"\nSuccessfully generated {len(LESSON_SPECS)} lessons! Index now has {len(updated_index)} modules.")

if __name__ == '__main__':
    main()
