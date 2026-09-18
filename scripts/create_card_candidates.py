"""
Build Candidate Flashcards for Lessons Dashboard
Generates rich, high-yield candidate flashcards for each curriculum lesson
strictly adhering to anki-card-generator skill rules:
- Romanized Hindi only (NO Devanagari)
- Macron / retroflex diacritics in #718096
- Word-by-word gloss in #2b6cb0
- Explicit Target Focus badge in #6b46c1
- Formality & gender markers in English front
- Contextual anchors (Shivani, Norwich, Toronto AI, music, improv)
- 100% novelty verification against deck_snapshot.json
"""

import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Candidate cards mapped by lesson code
CANDIDATE_CARDS = {
    "A0-01": [
        {
            "front": "I am completely ready for our trip. (<i>m</i>)",
            "back": "Main hamaare trip ke liye poora ready hoon.<br><br><span style=\"color: #718096;\"><i>Maiṁ hamāre trip ke liye pūrā ready hūṁ.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Maiṁ (I) | hamāre (our) | trip ke liye (for the trip) | pūrā (completely) | ready hūṁ (am ready)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-01] Pronouns & Present 'To Be' (main ... hoon)</small></span>",
            "target_focus": "Pronouns & Present 'To Be' (main ... hoon)"
        },
        {
            "front": "Are you also an engineer here? (<i>formal, m</i>)",
            "back": "Kyaa aap bhee yahaan engineer hain?<br><br><span style=\"color: #718096;\"><i>Kyā āp bhī yahāṁ engineer haiṁ?</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Kyā (question marker) | āp (you - formal) | bhī (also) | yahāṁ (here) | engineer haiṁ (are engineer)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-01] Formal subject pronoun & plural 'To Be' (aap ... hain)</small></span>",
            "target_focus": "Formal subject pronoun & plural 'To Be' (aap ... hain)"
        },
        {
            "front": "We are very happy today. (<i>m/general</i>)",
            "back": "Hum aaj bohot khush hain.<br><br><span style=\"color: #718096;\"><i>Hum āj bohot khush haiṁ.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Hum (we) | āj (today) | bohot (very) | khush haiṁ (are happy)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-01] First person plural (hum ... hain)</small></span>",
            "target_focus": "First person plural (hum ... hain)"
        },
        {
            "front": "How is your new team in Norwich? (<i>formal</i>)",
            "back": "Norwich mein aapkee nayi team kaisee hai?<br><br><span style=\"color: #718096;\"><i>Norwich meṁ āpkī nayī team kaisī hai?</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Norwich meṁ (in Norwich) | āpkī (your) | nayī team (new team) | kaisī hai (how is)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-01] Interrogative pronoun 'kaisee' with singular 'hai'</small></span>",
            "target_focus": "Interrogative pronoun 'kaisee' with singular 'hai'"
        },
        {
            "front": "Are you excited for the weekend comedy show? (<i>casual, f</i>)",
            "back": "Kyaa tum weekend comedy show ke liye excited ho?<br><br><span style=\"color: #718096;\"><i>Kyā tum weekend comedy show ke liye excited ho?</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Kyā (question marker) | tum (you - casual) | weekend comedy show ke liye (for weekend show) | excited ho (are excited)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-01] Casual 2nd-person address (tum ... ho)</small></span>",
            "target_focus": "Casual 2nd-person address (tum ... ho)"
        }
    ],
    "A0-02": [
        {
            "front": "I test new AI code on my laptop every morning. (<i>m</i>)",
            "back": "Main har subah apne laptop par nayaa AI code test kartaa hoon.<br><br><span style=\"color: #718096;\"><i>Maiṁ har subah apne laptop par nayā AI code test kartā hūṁ.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Maiṁ (I) | har subah (every morning) | apne laptop par (on my laptop) | nayā AI code (new AI code) | test kartā hūṁ (test - habit)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-02] Present Habitual routine (-taa hoon)</small></span>",
            "target_focus": "Present Habitual routine (-taa hoon)"
        },
        {
            "front": "Right now, I am tuning my electric guitar. (<i>m</i>)",
            "back": "Abhee main apnaa electric guitar tune kar rahaa hoon.<br><br><span style=\"color: #718096;\"><i>Abhī maiṁ apnā electric guitar tune kar rahā hūṁ.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Abhī (right now) | maiṁ (I) | apnā electric guitar (my electric guitar) | tune kar rahā hūṁ (am tuning)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-02] Present Continuous ongoing action (-rahaa hoon)</small></span>",
            "target_focus": "Present Continuous ongoing action (-rahaa hoon)"
        },
        {
            "front": "What kind of games do you play on weekends? (<i>casual, f</i>)",
            "back": "Tum weekends par kis tarah ke games kheltii ho?<br><br><span style=\"color: #718096;\"><i>Tum weekends par kis tarah ke games kheltī ho?</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Tum (you) | weekends par (on weekends) | kis tarah ke games (what kind of games) | kheltī ho (play - fem habit)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-02] Inquiring about habits with feminine agreement (-tii ho)</small></span>",
            "target_focus": "Inquiring about habits with feminine agreement (-tii ho)"
        },
        {
            "front": "Shivani is coordinating a music workshop right now. (<i>f</i>)",
            "back": "Shivani abhee ek music workshop coordinate kar rahee hai.<br><br><span style=\"color: #718096;\"><i>Shivani abhī ek music workshop coordinate kar rahī hai.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Shivani (Shivani) | abhī (right now) | ek music workshop (a music workshop) | coordinate kar rahī hai (is coordinating - fem cont)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-02] Feminine Present Continuous (rahee hai)</small></span>",
            "target_focus": "Feminine Present Continuous (rahee hai)"
        },
        {
            "front": "Do you often go for walks in the park? (<i>formal, m</i>)",
            "back": "Kyaa aap aksar park mein walk ke liye jaate hain?<br><br><span style=\"color: #718096;\"><i>Kyā āp aksar park meṁ walk ke liye jāte haiṁ?</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Kyā (question) | āp (you - formal) | aksar (often) | park meṁ (in park) | walk ke liye (for walk) | jāte haiṁ (go - formal habit)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-02] Formal Habitual question (jaate hain)</small></span>",
            "target_focus": "Formal Habitual question (jaate hain)"
        }
    ],
    "A0-03": [
        {
            "front": "I want to talk to you about the Norwich trip itinerary.",
            "back": "Main tumse Norwich trip ke itinerary ke baare mein baat karnaa chaahtaa hoon.<br><br><span style=\"color: #718096;\"><i>Maiṁ tumse Norwich trip ke itinerary ke bāre meṁ bāt karnā chāhtā hūṁ.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Maiṁ (I) | tumse (with you) | Norwich trip ke itinerary ke bāre meṁ (about Norwich trip itinerary) | bāt karnā chāhtā hūṁ (want to talk)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-03] Compound postposition 'ke baare mein' (about)</small></span>",
            "target_focus": "Compound postposition 'ke baare mein' (about)"
        },
        {
            "front": "The café is very cozy, but the coffee is a bit bitter.",
            "back": "Café bohot cozy hai, lekin coffee thodii kadvee hai.<br><br><span style=\"color: #718096;\"><i>Café bohot cozy hai, lekin coffee thoṛī kaṛvī hai.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Café (café) | bohot cozy hai (is very cozy) | lekin (but) | coffee (coffee) | thoṛī kaṛvī hai (is a bit bitter)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-03] Logical contrast connector 'lekin' (but)</small></span>",
            "target_focus": "Logical contrast connector 'lekin' (but)"
        },
        {
            "front": "I am carrying an umbrella because it might rain in the afternoon.",
            "back": "Main chhaataa le rahaa hoon kyunki dopahar ko baarish ho saktii hai.<br><br><span style=\"color: #718096;\"><i>Maiṁ chhātā le rahā hūṁ kyuṅki dopahar ko bārish ho saktī hai.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Maiṁ (I) | chhātā (umbrella) | le rahā hūṁ (am taking) | kyuṅki (because) | dopahar ko (in afternoon) | bārish ho saktī hai (rain can happen)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-03] Causal connector 'kyunki' (because)</small></span>",
            "target_focus": "Causal connector 'kyunki' (because)"
        },
        {
            "front": "By the way, who is coming to the pub with us tonight?",
            "back": "Vaise, aaj raat hamaare saath pub kaun aa rahaa hai?<br><br><span style=\"color: #718096;\"><i>Vaise, āj rāt hamāre sāth pub kaun ā rahā hai?</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Vaise (by the way) | āj rāt (tonight) | hamāre sāth (with us) | pub (pub) | kaun ā rahā hai (who is coming)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-03] Conversational opener 'vaise' & 'ke saath'</small></span>",
            "target_focus": "Conversational opener 'vaise' & 'ke saath'"
        },
        {
            "front": "I don't have enough time today, so we will meet tomorrow.",
            "back": "Mere paas aaj zyaadaa time nahin hai, isliye hum kal milenge.<br><br><span style=\"color: #718096;\"><i>Mere pās āj zyādā time nahīṁ hai, isliye hum kal mileṅge.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Mere pās (with me / I have) | āj (today) | zyādā time nahīṁ hai (not much time) | isliye (therefore) | hum (we) | kal mileṅge (will meet tomorrow)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-03] Possession marker 'ke paas' & consequence 'isliye'</small></span>",
            "target_focus": "Possession marker 'ke paas' & consequence 'isliye'"
        }
    ],
    "A0-04": [
        {
            "front": "Can you recommend a good vegetarian dish here? (<i>formal</i>)",
            "back": "Kyaa aap yahaan ek achhaa vegetarian dish recommend kar sakte hain?<br><br><span style=\"color: #718096;\"><i>Kyā āp yahāṁ ek achhā vegetarian dish recommend kar sakte haiṁ?</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Kyā (question) | āp (you - formal) | yahāṁ (here) | ek achhā dish (a good dish) | recommend kar sakte haiṁ (can recommend)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-04] Expressing polite ability / request (kar sakte hain)</small></span>",
            "target_focus": "Expressing polite ability / request (kar sakte hain)"
        },
        {
            "front": "I want to buy a train ticket to Norwich for next Friday. (<i>m</i>)",
            "back": "Main agle Friday ke liye Norwich kee train ticket khareednaa chaahtaa hoon.<br><br><span style=\"color: #718096;\"><i>Maiṁ agle Friday ke liye Norwich kī train ticket kharīdnā chāhtā hūṁ.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Maiṁ (I) | agle Friday ke liye (for next Friday) | Norwich kī train ticket (train ticket of Norwich) | kharīdnā chāhtā hūṁ (want to buy)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-04] Expressing intent with want to (khareednaa chaahtaa hoon)</small></span>",
            "target_focus": "Expressing intent with want to (khareednaa chaahtaa hoon)"
        },
        {
            "front": "I really need a glass of cold water right now.",
            "back": "Mujhe abhee ek glass thandaa paanee chaahiye.<br><br><span style=\"color: #718096;\"><i>Mujhe abhī ek glass ṭhaṇḍā pānī chāhiye.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Mujhe (to me) | abhī (right now) | ek glass ṭhaṇḍā pānī (a glass of cold water) | chāhiye (is needed)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-04] Expressing direct necessity with item (mujhe chaahiye)</small></span>",
            "target_focus": "Expressing direct necessity with item (mujhe chaahiye)"
        },
        {
            "front": "I really like the energy of this improv theater.",
            "back": "Mujhe is improv theater kee energy bohot pasand hai.<br><br><span style=\"color: #718096;\"><i>Mujhe is improv theater kī energy bohot pasand hai.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Mujhe (to me) | is improv theater kī energy (this improv theater's energy) | bohot pasand hai (is very liked)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-04] Expressing preference with 'pasand hai'</small></span>",
            "target_focus": "Expressing preference with 'pasand hai'"
        },
        {
            "front": "I don't know where the subway entrance is located.",
            "back": "Mujhe nahin pataa ki subway entrance kahaan hai.<br><br><span style=\"color: #718096;\"><i>Mujhe nahīṁ patā ki subway entrance kahāṁ hai.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Mujhe nahīṁ patā (to me not known) | ki (that) | subway entrance (subway entrance) | kahāṁ hai (where is)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-04] Stating lack of knowledge (mujhe nahin pataa)</small></span>",
            "target_focus": "Stating lack of knowledge (mujhe nahin pataa)"
        }
    ],
    "A0-05": [
        {
            "front": "Before ordering dinner, let's take a look at the cocktail menu.",
            "back": "Dinner order karne se pehle, chalo cocktail menu dekh lete hain.<br><br><span style=\"color: #718096;\"><i>Dinner order karne se pehle, chalo cocktail menu dekh lete haiṁ.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Dinner order karne se pehle (before ordering dinner - oblique) | chalo (let's) | cocktail menu (cocktail menu) | dekh lete haiṁ (take a look)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-05] Infinitive oblique shift before 'se pehle' (-ne se pehle)</small></span>",
            "target_focus": "Infinitive oblique shift before 'se pehle' (-ne se pehle)"
        },
        {
            "front": "There are many historical paintings in that old room.",
            "back": "Us puraane kamre mein kaee historical paintings hain.<br><br><span style=\"color: #718096;\"><i>Us purāne kamre meṁ kaī historical paintings haiṁ.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Us (that - oblique demonstrative) | purāne kamre meṁ (in old room - noun oblique) | kaī (several) | historical paintings haiṁ (are paintings)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-05] Demonstrative (vo->us) and noun (kamraa->kamre) oblique shift</small></span>",
            "target_focus": "Demonstrative (vo->us) and noun (kamraa->kamre) oblique shift"
        },
        {
            "front": "After attending the workshop, I will head straight home. (<i>m</i>)",
            "back": "Workshop attend karne ke baad, main seedhaa ghar jaaoongaa.<br><br><span style=\"color: #718096;\"><i>Workshop attend karne ke bād, maiṁ sīdhā ghar jāūṅgā.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Workshop attend karne ke bād (after attending workshop) | maiṁ (I) | sīdhā (straight) | ghar jāūṅgā (will go home)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-05] Infinitive oblique shift before 'ke baad' (-ne ke baad)</small></span>",
            "target_focus": "Infinitive oblique shift before 'ke baad' (-ne ke baad)"
        },
        {
            "front": "Which road should we take to reach the central market? (<i>formal</i>)",
            "back": "Central market jaane ke liye hamein kis raste par chalnaa chaahiye?<br><br><span style=\"color: #718096;\"><i>Central market jāne ke liye hameṁ kis raste par chalnā chāhiye?</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Central market jāne ke liye (for going) | hameṁ (to us) | kis raste par (on which road - oblique) | chalnā chāhiye (should walk)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-05] Interrogative pronoun oblique (kaun->kis) & noun shift (rastaa->raste)</small></span>",
            "target_focus": "Interrogative pronoun oblique (kaun->kis) & noun shift (rastaa->raste)"
        },
        {
            "front": "Please leave your heavy jacket in this corner. (<i>polite</i>)",
            "back": "Apnaa bhaarii jacket is kone mein chhod deejiye.<br><br><span style=\"color: #718096;\"><i>Apnā bhārī jacket is kone meṁ chhoṛ dījiye.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Apnā bhārī jacket (your heavy jacket) | is kone meṁ (in this corner - kona->kone) | chhoṛ dījiye (please leave)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-05] Proximal oblique demonstrative (ye->is) & noun shift</small></span>",
            "target_focus": "Proximal oblique demonstrative (ye->is) & noun shift"
        }
    ],
    "A0-06": [
        {
            "front": "I spoke with my AI project lead yesterday afternoon. (<i>m</i>)",
            "back": "Maine kal dopahar ko apne AI project lead se baat kee.<br><br><span style=\"color: #718096;\"><i>Maine kal dopahar ko apne AI project lead se bāt kī.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Maine (I - past transitive) | kal dopahar ko (yesterday afternoon) | apne AI project lead se (with my project lead) | bāt kī (spoke - fem)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-06] Completed past with light verb (baat kee)</small></span>",
            "target_focus": "Completed past with light verb (baat kee)"
        },
        {
            "front": "Did you understand the new improv game rules? (<i>casual, f</i>)",
            "back": "Kyaa tum naye improv game ke rules samajh gayī?<br><br><span style=\"color: #718096;\"><i>Kyā tum naye improv game ke rules samajh gayī?</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Kyā (question) | tum (you) | naye game ke rules (new game rules) | samajh gayī (understood - fem completed)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-06] Irregular compound past (samajh gayī)</small></span>",
            "target_focus": "Irregular compound past (samajh gayī)"
        },
        {
            "front": "Where did everyone go after the rehearsal? (<i>plural</i>)",
            "back": "Rehearsal ke baad sab log kahaan gaye?<br><br><span style=\"color: #718096;\"><i>Rehearsal ke bād sab log kahāṁ gaye?</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Rehearsal ke bād (after rehearsal) | sab log (all people) | kahāṁ gaye (where went - masc pl)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-06] Irregular past of jaanaa (gaye)</small></span>",
            "target_focus": "Irregular past of jaanaa (gaye)"
        },
        {
            "front": "Yesterday was a really productive day for our team.",
            "back": "Kal hamaari team ke liye ek bohot productive din thaa.<br><br><span style=\"color: #718096;\"><i>Kal hamārī team ke liye ek bohot productive din thā.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Kal (yesterday) | hamārī team ke liye (for our team) | ek bohot productive din (a very productive day) | thā (was - masc sing)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-06] Simple past of 'To Be' (thaa)</small></span>",
            "target_focus": "Simple past of 'To Be' (thaa)"
        },
        {
            "front": "A big parcel arrived at my door this morning.",
            "back": "Aaj subah mere darwaaze par ek badaa parcel aayaa.<br><br><span style=\"color: #718096;\"><i>Āj subah mere darvāze par ek baṛā parcel āyā.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Āj subah (this morning) | mere darvāze par (at my door) | ek baṛā parcel (a big parcel) | āyā (came/arrived - masc sing)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-06] Irregular completed past of aanaa (aayaa)</small></span>",
            "target_focus": "Irregular completed past of aanaa (aayaa)"
        }
    ],
    "A0-07": [
        {
            "front": "This new acoustic guitar sounds really sweet. (<i>m</i>)",
            "back": "Ye nayaa acoustic guitar bohot meethaa bajtaa hai.<br><br><span style=\"color: #718096;\"><i>Ye nayā acoustic guitar bohot mīṭhā bajtā hai.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Ye (this) | nayā guitar (new guitar - masc) | bohot mīṭhā (very sweet - masc adj) | bajtā hai (plays/sounds - masc verb)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-07] Masculine adjective-noun-verb harmony (-aa ... -aa ... -taa)</small></span>",
            "target_focus": "Masculine adjective-noun-verb harmony (-aa ... -aa ... -taa)"
        },
        {
            "front": "My close female friend tells great stories. (<i>f</i>)",
            "back": "Merī achhii dost bohot achhii kahaaniyaan sunaatii hai.<br><br><span style=\"color: #718096;\"><i>Merī achhī dost bohot achhī kahāniyāṁ sunātī hai.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Merī achhī dost (my good friend - fem) | bohot achhī kahāniyāṁ (very good stories - fem pl) | sunātī hai (tells/narrates - fem verb)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-07] Feminine gender agreement across possessive, adjective, and verb (-ii)</small></span>",
            "target_focus": "Feminine gender agreement across possessive, adjective, and verb (-ii)"
        },
        {
            "front": "All these sweet red apples are very fresh.",
            "back": "Ye sab meethe laal seb bohot taazaa hain.<br><br><span style=\"color: #718096;\"><i>Ye sab mīṭhe lāl seb bohot tāzā haiṁ.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Ye sab (all these) | mīṭhe lāl seb (sweet red apples - masc pl) | bohot tāzā haiṁ (are very fresh)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-07] Masculine plural adjective suffix (-e for plural marked adjectives)</small></span>",
            "target_focus": "Masculine plural adjective suffix (-e for plural marked adjectives)"
        },
        {
            "front": "The cold river water is very refreshing.",
            "back": "Nadee kaa thandaa paanee bohot refreshing hai.<br><br><span style=\"color: #718096;\"><i>Nadī kā ṭhaṇḍā pānī bohot refreshing hai.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Nadī kā (of river) | ṭhaṇḍā pānī (cold water - paanee is masc) | bohot refreshing hai (is very refreshing)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-07] Masculine noun agreement with 'paanee' (ṭhaṇḍā pānī, not ṭhaṇḍī)</small></span>",
            "target_focus": "Masculine noun agreement with 'paanee' (ṭhaṇḍā pānī, not ṭhaṇḍī)"
        },
        {
            "front": "Your white cat sleeps all afternoon. (<i>f</i>)",
            "back": "Aapkee safed billee pooree dopahar sotii hai.<br><br><span style=\"color: #718096;\"><i>Āpkī safed billī pūrī dopahar sotī hai.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Āpkī (your - fem) | safed billī (white cat - fem) | pūrī dopahar (entire afternoon - fem) | sotī hai (sleeps - fem verb)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-07] Full feminine concord chain (aapkee ... billee ... pooree ... sotii hai)</small></span>",
            "target_focus": "Full feminine concord chain (aapkee ... billee ... pooree ... sotii hai)"
        },
        {
            "front": "This big historic building looks amazing at night.",
            "back": "Ye badee puraanii building raat ko kamaal dikhtii hai.<br><br><span style=\"color: #718096;\"><i>Ye baṛī purānī building rāt ko kamāl dikhtī hai.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Ye (this) | baṛī purānī building (big old building - fem) | rāt ko (at night) | kamāl dikhtī hai (looks fantastic - fem)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-07] Treating loanword 'building' as feminine with harmonized adjectives (badee puraanii)</small></span>",
            "target_focus": "Treating loanword 'building' as feminine with harmonized adjectives (badee puraanii)"
        }
    ],
    "A0-08": [
        {
            "front": "I will board the evening train to Norwich at five o'clock. (<i>m</i>)",
            "back": "Main paanch baje Norwich kee shaam vaalee train pakdoongaa.<br><br><span style=\"color: #718096;\"><i>Maiṁ pāñch baje Norwich kī shām vālī train pakṛūṅgā.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Maiṁ (I) | pāñch baje (at 5 o'clock) | Norwich kī shām vālī train (Norwich's evening train) | pakṛūṅgā (will catch - masc fut)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-08] Simple Future 1st-person masculine (-ūngaa)</small></span>",
            "target_focus": "Simple Future 1st-person masculine (-ūngaa)"
        },
        {
            "front": "Will we perform our improv scene together next Sunday? (<i>plural</i>)",
            "back": "Kyaa hum agle Sunday ko apnaa improv scene ek saath perform karenge?<br><br><span style=\"color: #718096;\"><i>Kyā hum agle Sunday ko apnā improv scene ek sāth perform kareṅge?</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Kyā (question) | hum (we) | agle Sunday ko (next Sunday) | apnā improv scene (our improv scene) | ek sāth (together) | perform kareṅge (will perform)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-08] 1st-person plural future (-enge)</small></span>",
            "target_focus": "1st-person plural future (-enge)"
        },
        {
            "front": "What time will you arrive at the station? (<i>formal, f</i>)",
            "back": "Aap station par kitne baje aayengii?<br><br><span style=\"color: #718096;\"><i>Āp station par kitne baje āyeṅgī?</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Āp (you - formal) | station par (at station) | kitne baje (at what time) | āyeṅgī (will come - formal fem future)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-08] Formal feminine future ending (-engii)</small></span>",
            "target_focus": "Formal feminine future ending (-engii)"
        },
        {
            "front": "I will send you the pub's Google Maps pin in ten minutes. (<i>m</i>)",
            "back": "Main das minute mein tumhein pub kee Google Maps pin bhejūngaa.<br><br><span style=\"color: #718096;\"><i>Maiṁ das minute meṁ tumheṁ pub kī Google Maps pin bhejūṅgā.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Maiṁ (I) | das minute meṁ (in 10 mins) | tumheṁ (to you) | pub kī Maps pin (pub's pin) | bhejūṅgā (will send - masc)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-08] Immediate commitment in future (-ūngaa)</small></span>",
            "target_focus": "Immediate commitment in future (-ūngaa)"
        },
        {
            "front": "Will you try this spicy curry with us? (<i>casual, f</i>)",
            "back": "Kyaa tum hamaare saath ye teekhee curry try karogii?<br><br><span style=\"color: #718096;\"><i>Kyā tum hamāre sāth ye tīkhī curry try karogī?</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Kyā (question) | tum (you - casual) | hamāre sāth (with us) | ye tīkhī curry (this spicy curry) | try karogī (will try - fem casual future)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-08] Casual feminine future ending (-ogii)</small></span>",
            "target_focus": "Casual feminine future ending (-ogii)"
        }
    ],
    "A1-01": [
        {
            "front": "Please take a seat right here and relax. (<i>polite</i>)",
            "back": "Kripya yahaan baithiye aur aaraam keejiye.<br><br><span style=\"color: #718096;\"><i>Kripayā yahāṁ baiṭhiye aur ārām kījiye.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Kripayā (please) | yahāṁ (here) | baiṭhiye (please sit - polite) | aur (and) | ārām kījiye (please rest/relax - polite)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-01] Formal imperative suffix (-iye)</small></span>",
            "target_focus": "Formal imperative suffix (-iye)"
        },
        {
            "front": "Turn left at the traffic light and stop near the post office. (<i>casual</i>)",
            "back": "Traffic light par baayein mudo aur post office ke paas ruko.<br><br><span style=\"color: #718096;\"><i>Traffic light par bāyeṁ muṛo aur post office ke pās ruko.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Traffic light par (at traffic light) | bāyeṁ muṛo (turn left - casual) | aur (and) | post office ke pās ruko (stop near post office)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-01] Directional vocabulary & casual imperative (-o)</small></span>",
            "target_focus": "Directional vocabulary & casual imperative (-o)"
        },
        {
            "front": "Don't worry about the train delay at all. (<i>casual</i>)",
            "back": "Train ke delay ke baare mein bilkul chintaa mat karo.<br><br><span style=\"color: #718096;\"><i>Train ke delay ke bāre meṁ bilkul chintā mat karo.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Train ke delay ke bāre meṁ (about train delay) | bilkul (at all) | chintā mat karo (don't worry - mat + imperative)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-01] Negative imperative with 'mat'</small></span>",
            "target_focus": "Negative imperative with 'mat'"
        },
        {
            "front": "Please taste this homemade dip before lunch. (<i>polite</i>)",
            "back": "Lunch se pehle ye homemade dip zaroor chakhiye.<br><br><span style=\"color: #718096;\"><i>Lunch se pehle ye homemade dip zarūr chakhiye.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Lunch se pehle (before lunch) | ye homemade dip (this dip) | zarūr (definitely) | chakhiye (please taste - polite)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-01] Polite imperative offering (chakhiye)</small></span>",
            "target_focus": "Polite imperative offering (chakhiye)"
        },
        {
            "front": "Pass me the salt shaker from across the table. (<i>casual</i>)",
            "back": "Table ke doosre side se namak idhar badhaao.<br><br><span style=\"color: #718096;\"><i>Table ke dūsre side se namak idhar baṛhāo.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Table ke dūsre side se (from table's other side) | namak (salt) | idhar baṛhāo (pass/forward here - casual)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-01] Casual transitive imperative (-o)</small></span>",
            "target_focus": "Casual transitive imperative (-o)"
        }
    ],
    "A1-02": [
        {
            "front": "My elder brother lives in Toronto with his family.",
            "back": "Mere bade bhaai apne parivaar ke saath Toronto mein rahte hain.<br><br><span style=\"color: #718096;\"><i>Mere baṛe bhāī apne parivār ke sāth Toronto meṁ rahte haiṁ.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Mere baṛe bhāī (my elder brother - honorific plural) | apne parivār ke sāth (with his family) | Toronto meṁ rahte haiṁ (lives in Toronto)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-02] Possessive pronoun & honorific agreement (mere bade bhaai)</small></span>",
            "target_focus": "Possessive pronoun & honorific agreement (mere bade bhaai)"
        },
        {
            "front": "Is this your younger sister's camera bag? (<i>formal</i>)",
            "back": "Kyaa ye aapkee chhotee bahan kaa camera bag hai?<br><br><span style=\"color: #718096;\"><i>Kyā ye āpkī chhoṭī bahan kā camera bag hai?</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Kyā (question) | ye (this) | āpkī chhoṭī bahan kā (of your younger sister) | camera bag hai (is camera bag - masc)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-02] Nested possessive agreement (aapkī bahan kaa bag)</small></span>",
            "target_focus": "Nested possessive agreement (aapkī bahan kaa bag)"
        },
        {
            "front": "Shivani's workplace in Norwich has a lovely garden.",
            "back": "Norwich mein Shivani ke office kaa ek pyaaraa garden hai.<br><br><span style=\"color: #718096;\"><i>Norwich meṁ Shivani ke office kā ek pyārā garden hai.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Norwich meṁ (in Norwich) | Shivani ke office kā (of Shivani's office) | ek pyārā garden hai (is a lovely garden - masc)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-02] Possessive postposition 'kaa/ke' matching target noun (garden -> kaa)</small></span>",
            "target_focus": "Possessive postposition 'kaa/ke' matching target noun (garden -> kaa)"
        },
        {
            "front": "Where are your grandparents staying these days? (<i>formal</i>)",
            "back": "Aapke daadaa-daadee in dinon kahaan rah rahe hain?<br><br><span style=\"color: #718096;\"><i>Āpke dādā-dādī in dinoṁ kahāṁ rah rahe haiṁ?</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Āpke dādā-dādī (your grandparents - respectful masc pl) | in dinoṁ (these days) | kahāṁ rah rahe haiṁ (where are staying)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-02] Family kinship vocabulary & plural possessive (aapke)</small></span>",
            "target_focus": "Family kinship vocabulary & plural possessive (aapke)"
        },
        {
            "front": "My friend's dog always barks at postal deliveries.",
            "back": "Mere dost kaa kuttaa hameshaa deliveries par bhonktaa hai.<br><br><span style=\"color: #718096;\"><i>Mere dost kā kuttā hameshā deliveries par bhōṅktā hai.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Mere dost kā kuttā (my friend's dog - masc) | hameshā (always) | deliveries par (at deliveries) | bhōṅktā hai (barks)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-02] Associative postposition agreement (mere dost kaa kuttā)</small></span>",
            "target_focus": "Associative postposition agreement (mere dost kaa kuttā)"
        }
    ],
    "A1-03": [
        {
            "front": "I believe that this local comedy club will be packed tonight.",
            "back": "Mujhe lagtaa hai ki ye local comedy club aaj raat packed hogaa.<br><br><span style=\"color: #718096;\"><i>Mujhe lagtā hai ki ye local comedy club āj rāt packed hogā.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Mujhe lagtā hai (it seems to me) | ki (that - subordinating conjunction) | ye local comedy club (this local club) | āj rāt packed hogā (will be packed tonight)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-03] Subordinating conjunction 'ki' expressing impression / belief</small></span>",
            "target_focus": "Subordinating conjunction 'ki' expressing impression / belief"
        },
        {
            "front": "Shivani mentioned that Norwich castle has an impressive museum.",
            "back": "Shivani ne bataayaa ki Norwich castle mein ek shaandaar museum hai.<br><br><span style=\"color: #718096;\"><i>Shivani ne batāyā ki Norwich castle meṁ ek shāndār museum hai.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Shivani ne batāyā (Shivani shared/said) | ki (that) | Norwich castle meṁ (in Norwich castle) | ek shāndār museum hai (is an impressive museum)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-03] Reported speech clause linked by 'ki'</small></span>",
            "target_focus": "Reported speech clause linked by 'ki'"
        },
        {
            "front": "Do you think that the weather will stay sunny this weekend? (<i>casual, f</i>)",
            "back": "Kyaa tumhein lagtaa hai ki is weekend mausam dhoop vaalaa rahegaa?<br><br><span style=\"color: #718096;\"><i>Kyā tumheṁ lagtā hai ki is weekend mausam dhūp vālā rahegā?</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Kyā tumheṁ lagtā hai (do you feel) | ki (that) | is weekend (this weekend) | mausam (weather) | dhūp vālā rahegā (will remain sunny)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-03] Interrogative opinion clause with conjunction 'ki'</small></span>",
            "target_focus": "Interrogative opinion clause with conjunction 'ki'"
        },
        {
            "front": "I heard that the ticket price of the London express increased.",
            "back": "Maine sunaa ki London express kee ticket kaa daam badh gayaa.<br><br><span style=\"color: #718096;\"><i>Maine sunā ki London express kī ticket kā dām baṛh gayā.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Maine sunā (I heard) | ki (that - conjunction) | London express kī ticket kā dām (ticket price of London express - possessive) | baṛh gayā (increased)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-03] Dual contrast: subordinating 'ki' (that) vs possessive 'kee/kaa' (of)</small></span>",
            "target_focus": "Dual contrast: subordinating 'ki' (that) vs possessive 'kee/kaa' (of)"
        },
        {
            "front": "My manager told me that our new AI project will launch in October.",
            "back": "Mere manager ne kahaa ki hamaaraa nayaa AI project October mein launch hogaa.<br><br><span style=\"color: #718096;\"><i>Mere manager ne kahā ki hamārā nayā AI project October meṁ launch hogā.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Mere manager ne kahā (my manager said) | ki (that) | hamārā nayā AI project (our new AI project) | October meṁ launch hogā (will launch in Oct)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-03] Workplace reported speech with conjunction 'ki'</small></span>",
            "target_focus": "Workplace reported speech with conjunction 'ki'"
        }
    ],
    "A1-04": [
        {
            "front": "I have to finish reviewing this pull request before leaving the office. (<i>m</i>)",
            "back": "Office se nikalne se pehle mujhe ye pull request review karnaa hai.<br><br><span style=\"color: #718096;\"><i>Office se nikalne se pehle mujhe ye pull request review karnā hai.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Office se nikalne se pehle (before leaving office) | mujhe (to me) | ye pull request (this PR) | review karnā hai (have to review - personal necessity)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-04] Personal necessity / scheduled obligation (infinitive + hai)</small></span>",
            "target_focus": "Personal necessity / scheduled obligation (infinitive + hai)"
        },
        {
            "front": "In the UK, you have to drive on the left side of the road.",
            "back": "UK mein road ke baayein taraf drive karnaa padtaa hai.<br><br><span style=\"color: #718096;\"><i>UK meṁ road ke bāyeṁ taraf drive karnā paṛtā hai.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>UK meṁ (in the UK) | road ke bāyeṁ taraf (on left side of road) | drive karnā paṛtā hai (one has to drive - external law/rule)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-04] External societal / legal compulsion (padtaa hai)</small></span>",
            "target_focus": "External societal / legal compulsion (padtaa hai)"
        },
        {
            "front": "May I plug in my laptop charger here? (<i>polite permission</i>)",
            "back": "Kyaa main yahaan apnaa laptop charger lagaa saktaa hoon?<br><br><span style=\"color: #718096;\"><i>Kyā maiṁ yahāṁ apnā laptop charger lagā saktā hūṁ?</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Kyā maiṁ (may I) | yahāṁ (here) | apnā laptop charger (my laptop charger) | lagā saktā hūṁ (can plug in)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-04] Seeking courteous permission (kyaa main ... saktaa hoon)</small></span>",
            "target_focus": "Seeking courteous permission (kyaa main ... saktaa hoon)"
        },
        {
            "front": "Because of rain, we will have to reschedule our outdoor photoshoot.",
            "back": "Baarish kee vajah se hamein apnaa outdoor photoshoot reschedule karnaa padegaa.<br><br><span style=\"color: #718096;\"><i>Bārish kī vajah se hameṁ apnā outdoor photoshoot reschedule karnā paṛegā.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Bārish kī vajah se (due to rain) | hameṁ (to us) | apnā outdoor photoshoot (our outdoor photoshoot) | reschedule karnā paṛegā (will have to reschedule)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-04] Future unavoidable compulsion (padegaa)</small></span>",
            "target_focus": "Future unavoidable compulsion (padegaa)"
        },
        {
            "front": "I have to catch the morning train tomorrow at 6 AM sharp.",
            "back": "Mujhe kal subah theek chhah baje subah kee train pakadnee hai.<br><br><span style=\"color: #718096;\"><i>Mujhe kal subah ṭhīk chhah baje subah kī train pakaṛnī hai.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Mujhe (to me) | kal subah ṭhīk chhah baje (tomorrow sharp 6am) | subah kī train (morning train - fem) | pakaṛnī hai (have to catch - fem infinitive agreement)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-04] Feminine infinitive agreement with obligation object (train pakadnee hai)</small></span>",
            "target_focus": "Feminine infinitive agreement with obligation object (train pakadnee hai)"
        }
    ],
    "A1-05": [
        {
            "front": "I was writing some Python scripts when your phone call arrived. (<i>m</i>)",
            "back": "Jab tumhaaraa phone aayaa, tab main kuchh Python scripts likh rahaa thaa.<br><br><span style=\"color: #718096;\"><i>Jab tumhārā phone āyā, tab maiṁ kuchh Python scripts likh rahā thā.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Jab tumhārā phone āyā (when your call came) | tab (then) | maiṁ (I) | kuchh Python scripts (some Python scripts) | likh rahā thā (was writing - masc past cont)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-05] Past Continuous interrupted action (rahaa thaa)</small></span>",
            "target_focus": "Past Continuous interrupted action (rahaa thaa)"
        },
        {
            "front": "Shivani was preparing tea in her Norwich kitchen. (<i>f</i>)",
            "back": "Shivani apne Norwich ke kitchen mein chaay banaa rahee thee.<br><br><span style=\"color: #718096;\"><i>Shivani apne Norwich ke kitchen meṁ chāy banā rahī thī.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Shivani (Shivani) | apne Norwich ke kitchen meṁ (in her Norwich kitchen) | chāy (tea) | banā rahī thī (was making - fem past cont)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-05] Feminine Past Continuous (rahee thee)</small></span>",
            "target_focus": "Feminine Past Continuous (rahee thee)"
        },
        {
            "front": "Back in university, we used to practice improv scenes every Thursday night.",
            "back": "University ke dino mein hum har Thursday raat improv scenes practice karte the.<br><br><span style=\"color: #718096;\"><i>University ke dino meṁ hum har Thursday rāt improv scenes practice karte the.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>University ke dino meṁ (in university days) | hum (we) | har Thursday rāt (every Thursday night) | improv scenes (improv scenes) | practice karte the (used to practice - habitual past)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-05] Habitual Past routine (-te the)</small></span>",
            "target_focus": "Habitual Past routine (-te the)"
        },
        {
            "front": "Earlier, I used to play the piano for two hours every evening. (<i>m</i>)",
            "back": "Pehle main har shaam do ghante piano bajaataa thaa.<br><br><span style=\"color: #718096;\"><i>Pehle maiṁ har shām do ghaṇṭe piano bajātā thā.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Pehle (earlier) | maiṁ (I) | har shām (every evening) | do ghaṇṭe (two hours) | piano bajātā thā (used to play piano - masc habitual past)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-05] 1st-person masculine habitual past (-taa thaa)</small></span>",
            "target_focus": "1st-person masculine habitual past (-taa thaa)"
        },
        {
            "front": "Were you living in Toronto during that winter? (<i>casual, f</i>)",
            "back": "Kyaa tum us winter ke dauraan Toronto mein rah rahee theen?<br><br><span style=\"color: #718096;\"><i>Kyā tum us winter ke daurān Toronto meṁ rah rahī thīṁ?</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Kyā (question) | tum (you) | us winter ke daurān (during that winter) | Toronto meṁ (in Toronto) | rah rahī thīṁ (were living - fem past continuous)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-05] Feminine continuous past inquiry (rah rahee theen)</small></span>",
            "target_focus": "Feminine continuous past inquiry (rah rahee theen)"
        },
        {
            "front": "We used to hang out at that cozy pub after our weekend shows.",
            "back": "Weekend shows ke baad hum us cozy pub mein hang out karte the.<br><br><span style=\"color: #718096;\"><i>Weekend shows ke bād hum us cozy pub meṁ hang out karte the.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Weekend shows ke bād (after weekend shows) | hum (we) | us cozy pub meṁ (in that cozy pub) | hang out karte the (used to hang out - habitual past)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-05] Habitual past narration of university memories (-te the)</small></span>",
            "target_focus": "Habitual past narration of university memories (-te the)"
        }
    ],
    "A1-06": [
        {
            "front": "Could you please tell me how to get to the cathedral from here? (<i>polite</i>)",
            "back": "Kyaa aap bataayenge ki yahaan se cathedral kaise pahunchein?<br><br><span style=\"color: #718096;\"><i>Kyā āp batāyeṅge ki yahāṁ se cathedral kaise pahuñcheṁ?</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Kyā āp batāyeṅge (would you tell - polite) | ki (that) | yahāṁ se (from here) | cathedral (cathedral) | kaise pahuñcheṁ (how to reach)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-06] Polite inquiry using 'bataana' (bataayenge)</small></span>",
            "target_focus": "Polite inquiry using 'bataana' (bataayenge)"
        },
        {
            "front": "I spoke with the lifestyle coordinator about organizing an art session. (<i>m</i>)",
            "back": "Maine art session organize karne ke baare mein lifestyle coordinator se baat kee.<br><br><span style=\"color: #718096;\"><i>Maine art session organize karne ke bāre meṁ lifestyle coordinator se bāt kī.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Maine (I) | art session organize karne ke bāre meṁ (about organizing art session) | lifestyle coordinator se (with lifestyle coordinator) | bāt kī (spoke)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-06] Communication verb 'baat karna' with postposition 'se'</small></span>",
            "target_focus": "Communication verb 'baat karna' with postposition 'se'"
        },
        {
            "front": "Speak a bit slower, please, so I can catch every word. (<i>polite</i>)",
            "back": "Thodaa dheere boliye taaki main har shabd samajh sakoon.<br><br><span style=\"color: #718096;\"><i>Thoṛā dhīre boliye tāki maiṁ har shabd samajh sakūṁ.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Thoṛā dhīre boliye (please speak a bit slower) | tāki (so that) | maiṁ (I) | har shabd (every word) | samajh sakūṁ (can understand)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-06] Manner adverb with polite communication imperative (boliye)</small></span>",
            "target_focus": "Manner adverb with polite communication imperative (boliye)"
        },
        {
            "front": "What did the store manager say about the refund? (<i>polite</i>)",
            "back": "Store manager ne refund ke baare mein kyaa kahaa?<br><br><span style=\"color: #718096;\"><i>Store manager ne refund ke bāre meṁ kyā kahā?</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Store manager ne (store manager) | refund ke bāre meṁ (about the refund) | kyā kahā (what said - past of kehna)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-06] Transitive past communication verb 'kehna' (kahaa)</small></span>",
            "target_focus": "Transitive past communication verb 'kehna' (kahaa)"
        },
        {
            "front": "Tell me all the details about your new apartment in Norwich! (<i>casual</i>)",
            "back": "Norwich mein apne naye apartment kee pooree details bataao!<br><br><span style=\"color: #718096;\"><i>Norwich meṁ apne naye apartment kī pūrī details batāo!</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Norwich meṁ (in Norwich) | apne naye apartment kī (of your new apartment) | pūrī details (full details) | batāo (tell/share - casual imperative)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A1-06] Casual communicative imperative 'bataao'</small></span>",
            "target_focus": "Casual communicative imperative 'bataao'"
        }
    ]
}

def verify_and_save():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lessons-dashboard", "data"))
    deck_path = os.path.join(base_dir, "deck_snapshot.json")

    with open(deck_path, "r", encoding="utf-8") as f:
        deck = json.load(f)

    existing_fronts = [c["front"].lower().strip() for c in deck["cards"]]

    total_candidates = 0
    collisions = []

    for lesson_code, cards in CANDIDATE_CARDS.items():
        for c in cards:
            total_candidates += 1
            f_clean = c["front"].lower().strip()

            # Novelty check
            for ef in existing_fronts:
                if f_clean == ef or (len(f_clean) > 20 and f_clean in ef):
                    collisions.append((lesson_code, "Front collision", c["front"], ef))
            
            # Verify required formatting elements
            assert "#718096" in c["back"], f"Missing diacritics line in {c['front']}"
            assert "#2b6cb0" in c["back"], f"Missing gloss line in {c['front']}"
            assert "#6b46c1" in c["back"], f"Missing target badge line in {c['front']}"
            assert not re.search(r'[\u0900-\u097F]', c["back"]), f"Devanagari detected in {c['front']}"

    print(f"Total Candidate Cards Verified: {total_candidates}")
    print(f"Deck Collisions Found: {len(collisions)}")
    if collisions:
        for col in collisions:
            print("  COLLISION:", col)
        sys.exit(1)

    # Write candidates to JSON
    json_path = os.path.join(base_dir, "generated_card_candidates.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(CANDIDATE_CARDS, f, indent=2, ensure_ascii=False)
    print(f"Wrote JSON to {json_path}")

    # Write candidates to JS
    js_path = os.path.join(base_dir, "generated_card_candidates.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("// Candidate cards bank for in-app generation modal\n")
        f.write("window.CARD_CANDIDATES = " + json.dumps(CANDIDATE_CARDS, indent=2, ensure_ascii=False) + ";\n")
    print(f"Wrote JS to {js_path}")

if __name__ == "__main__":
    verify_and_save()
