"""Build the browser-ready animation catalog from curated source data.

The large string and list constants are deliberately kept as reviewable source data.
The pipeline below normalizes titles, merges aliases, assigns stable IDs, derives
content and quality scores, and writes both public catalog formats.
"""

import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
with open(ROOT / "data/original-v1.json", encoding="utf-8") as source_file:
    OLD = json.load(source_file)

# Former exclusions that were only excluded because of the old genre/taste rule.
REINSTATE={
'Spy x Family','Fruits Basket (2019)','Clannad / After Story','Horimiya','My Dress-Up Darling','Toradora!',
'Kaguya-sama: Love Is War','Violet Evergarden','Mushishi',"Natsume's Book of Friends",'Laid-Back Camp',
'March Comes in Like a Lion','Your Lie in April','A Silent Voice','Your Name','Weathering With You','The Garden of Words','Anohana'
}

# Broad, genre-neutral additions. These are recommendations, not a dump of every anime ever made.
# Format: Title | Year | Type | Origin | Curated tags | Quality band | Optional note
EXTRA = r'''
# --- Essential / all-time additions ---
Violet Evergarden | 2018 | Series | Japan | Drama, Emotional, Fantasy | S+ | Extraordinary audiovisual craft and emotional payoff.
Your Name | 2016 | Film | Japan | Romance, Drama, Supernatural | S+ | A blockbuster romance with momentum, mystery and huge emotional payoff.
A Silent Voice | 2016 | Film | Japan | Drama, Coming-of-age | S+ | Intimate character drama with exceptional direction and visual storytelling.
Kaguya-sama: Love Is War | 2019 | Series | Japan | Romance, Comedy | S+ | Romance structured like psychological warfare; consistently inventive and funny.
March Comes in Like a Lion | 2016 | Series | Japan | Drama, Coming-of-age | S+ | Slow when it needs to be, but never empty; some of anime's strongest character writing.
Mushishi | 2005 | Series | Japan | Supernatural, Mystery, Atmospheric | S+ | Meditative episodic storytelling with remarkable atmosphere and ideas.
The Tatami Galaxy | 2010 | Series | Japan | Comedy, Romance, Surreal | S+ | Hyperverbal, formally inventive and one of anime's smartest compact series.
Showa Genroku Rakugo Shinju | 2016 | Series | Japan | Historical, Drama, Performance | S+ | Adult character drama with decades of consequences and superb performances.
Chihayafuru | 2011 | Series | Japan | Sports, Drama, Romance | S+ | Competition, character growth and romantic tension with battle-anime intensity.
Bocchi the Rock! | 2022 | Series | Japan | Comedy, Music, Coming-of-age | S+ | Visual comedy constantly reinvents itself around an excellent band story.
A Place Further Than the Universe | 2018 | Series | Japan | Adventure, Drama, Friendship | S+ | A compact expedition story with momentum and earned emotional peaks.
Ping Pong the Animation | 2014 | Series | Japan | Sports, Drama | S+ | A complete character study disguised as a sports anime.
Millennium Actress | 2001 | Film | Japan | Drama, Romance, Meta | S+ | Satoshi Kon turns a life, a filmography and a love story into one fluid memory.
Tokyo Godfathers | 2003 | Film | Japan | Drama, Comedy | S+ | Fast, humane and funny without becoming sentimental mush.
The Tale of the Princess Kaguya | 2013 | Film | Japan | Fantasy, Drama | S+ | One of animation's great visual achievements and a devastating fable.
Grave of the Fireflies | 1988 | Film | Japan | War, Drama | S+ | Devastating anti-war drama with no wasted sentiment.
Wolf Children | 2012 | Film | Japan | Drama, Fantasy, Family | S+ | Family drama with genuine scope, visual beauty and an earned emotional arc.
The Girl Who Leapt Through Time | 2006 | Film | Japan | Sci-Fi, Romance, Coming-of-age | S+ | Time travel, comedy and regret in a near-perfect feature-length package.
The Disappearance of Haruhi Suzumiya | 2010 | Film | Japan | Sci-Fi, Mystery, Drama | S+ | A franchise payoff film that turns Haruhi into a serious emotional mystery.
K-On! | 2009 | Series | Japan | Music, Comedy, Slice-of-life | S | The benchmark for character-driven slice-of-life; relaxed but never lifeless.
Sound! Euphonium | 2015 | Series | Japan | Music, Drama, School | S+ | Meticulous musical drama with real competition, ambition and emotional tension.
Liz and the Blue Bird | 2018 | Film | Japan | Music, Drama | S+ | Naoko Yamada's extraordinarily precise, almost tactile character filmmaking.
Hyouka | 2012 | Series | Japan | Mystery, School, Drama | S | Small mysteries elevated by exceptional direction and character chemistry.
The Melancholy of Haruhi Suzumiya | 2006 | Series | Japan | Sci-Fi, Comedy, School | S | A landmark high-concept school comedy with one of anime's most unusual watch-order histories.
Nichijou | 2011 | Series | Japan | Comedy, Slice-of-life, Surreal | S | Absurdist comedy animated with ridiculous technical ambition.
Fruits Basket (2019) | 2019 | Series | Japan | Drama, Romance, Supernatural | S | A long-form emotional drama that actually pays off its huge ensemble.
Clannad / After Story | 2007 | Series | Japan | Drama, Romance, Supernatural | S | The first half is patient; After Story is why it remains an emotional landmark.
Nana | 2006 | Series | Japan | Drama, Romance, Music | S | Messy adult relationships treated with uncommon honesty and momentum.
Revolutionary Girl Utena | 1997 | Series | Japan | Drama, Fantasy, Psychological | S+ | Symbolic, strange and massively influential without being merely homework.
Princess Tutu | 2002 | Series | Japan | Fantasy, Drama, Romance | S | Starts like a fairy tale and becomes an intricate story about narrative fate.
Haibane Renmei | 2002 | Series | Japan | Fantasy, Drama, Mystery | S | Quiet, compact and emotionally resonant rather than merely slow.
Kino's Journey (2003) | 2003 | Series | Japan | Adventure, Philosophy, Anthology | S | Philosophical travel stories that stay concise and sharply constructed.
Welcome to the N.H.K. | 2006 | Series | Japan | Dark Comedy, Drama, Psychological | S | Uncomfortable, funny and painfully perceptive character drama.
The Twelve Kingdoms | 2002 | Series | Japan | Fantasy, Adventure, Politics | S | Deep political fantasy with one of anime's strongest growth arcs.
Moribito: Guardian of the Spirit | 2007 | Series | Japan | Fantasy, Action, Adventure | S | Mature fantasy adventure with superb animation and worldbuilding.
Shirobako | 2014 | Series | Japan | Workplace, Comedy, Drama | S | A genuinely entertaining look at how anime gets made.
Keep Your Hands Off Eizouken! | 2020 | Series | Japan | Comedy, Creativity, School | S | Animation itself becomes the adventure; visually inventive every episode.
Girls Band Cry | 2024 | Series | Japan | Music, Drama | S | Sharp character conflict and unusually expressive CG performance animation.
Nodame Cantabile | 2007 | Series | Japan | Music, Romance, Comedy | S | Classical music, adult ambition and comedy with strong forward motion.
Kids on the Slope | 2012 | Series | Japan | Music, Drama, Coming-of-age | S | Jazz performance and volatile friendship directed with real energy.
Run with the Wind | 2018 | Series | Japan | Sports, Drama | S | One of the best sports ensemble arcs, built around adults rather than prodigies.
Slam Dunk | 1993 | Series | Japan | Sports, Comedy, Basketball | S | Foundational sports anime with huge character payoff; the pacing is old-school but the core works.
Ashita no Joe | 1970 | Series | Japan | Boxing, Drama, Classic | S+ | A foundational sports tragedy whose character work still lands.
Cross Game | 2009 | Series | Japan | Baseball, Drama, Romance | S | Sports and grief folded into an exceptionally clean long-form story.
Space Brothers | 2012 | Series | Japan | Space, Drama, Workplace | S | Adult aspiration and aerospace detail with unusually likable long-form storytelling.
Planetes | 2003 | Series | Japan | Sci-Fi, Workplace, Drama | S+ | Hard-ish sci-fi, labor politics and adult character arcs in one complete story.
The Rose of Versailles | 1979 | Series | Japan | Historical, Drama, Romance | S+ | Sweeping political melodrama that helped define shoujo anime.
Future Boy Conan | 1978 | Series | Japan | Adventure, Sci-Fi, Classic | S | Miyazaki television adventure with exceptional momentum and visual invention.
Gunbuster | 1988 | OVA | Japan | Mecha, Sci-Fi, Drama | S+ | Six episodes that evolve from parody to genuinely enormous science-fiction emotion.
Macross Plus | 1994 | OVA | Japan | Mecha, Music, Sci-Fi | S+ | Watanabe/Kawamori-era audiovisual spectacle with an adult triangle and phenomenal flight animation.
Patlabor: The Movie | 1989 | Film | Japan | Mecha, Police, Thriller | S | Smart procedural mecha directed like a grounded techno-thriller.
Mobile Suit Gundam 0080: War in the Pocket | 1989 | OVA | Japan | Mecha, War, Drama | S+ | Compact anti-war Gundam that works even if you are not a franchise expert.
Mobile Suit Gundam: Char's Counterattack | 1988 | Film | Japan | Mecha, War, Sci-Fi | S | The major Amuro/Char culmination; essential after the early Universal Century core.
Mobile Suit Gundam Unicorn | 2010 | OVA | Japan | Mecha, War, Sci-Fi | S | Lavish Universal Century continuation with spectacular production.
Turn A Gundam | 1999 | Series | Japan | Mecha, Sci-Fi, Drama | S | Strange, humane and visually distinctive Gundam from Yoshiyuki Tomino.
Mobile Suit Gundam 00 | 2007 | Series | Japan | Mecha, War, Politics | S | A strong standalone Gundam entry built around interventionism and shifting alliances.
Eureka Seven | 2005 | Series | Japan | Mecha, Romance, Adventure | S | A long coming-of-age mecha adventure with memorable worldbuilding and music.
The Vision of Escaflowne | 1996 | Series | Japan | Fantasy, Mecha, Romance | S | Fantasy, romance and mecha fused with a terrific Yoko Kanno score.
RahXephon | 2002 | Series | Japan | Mecha, Mystery, Drama | S | Dense but rewarding psychological mecha with excellent audiovisual craft.
Dennou Coil | 2007 | Series | Japan | Sci-Fi, Mystery, Childhood | S | Augmented-reality adventure that becomes increasingly eerie and emotionally rich.
Kaiba | 2008 | Series | Japan | Sci-Fi, Romance, Surreal | S | Wild visual simplicity hiding a dense story about memory, bodies and class.
Time of Eve | 2008 | ONA | Japan | Sci-Fi, Drama, AI | S | Compact AI ethics drama with strong dialogue and a satisfying feature cut.
Astra Lost in Space | 2019 | Series | Japan | Sci-Fi, Adventure, Mystery | S | A complete space survival mystery that keeps moving and actually resolves itself.
Space Battleship Yamato 2199 | 2012 | Series | Japan | Space Opera, War, Sci-Fi | S | Modernized classic space opera with strong production and clean momentum.
Mobile Suit Gundam GQuuuuuuX | 2025 | Series | Japan | Mecha, Sci-Fi, Alternate History | S | A bold Gundam remix with high-end visual direction and major 2026 award recognition.
Witch Hat Atelier | 2026 | Series | Japan | Fantasy, Magic, Drama | S | A 2026 standout praised for unusually beautiful fantasy direction.
Daemons of the Shadow Realm | 2026 | Series | Japan | Fantasy, Action, Mystery | S | Fast, strange and already one of 2026's notable new adaptations.
Sentenced to Be a Hero | 2026 | Series | Japan | Dark Fantasy, Action | A+ | A surprisingly lavish 2026 fantasy production with a strong hook.
Steel Ball Run: JoJo's Bizarre Adventure | 2026 | Series | Japan | Adventure, Action, Western | S | A major JoJo adaptation and one of 2026's biggest continuing franchise events.
Frieren: Beyond Journey's End Season 2 | 2026 | Series | Japan | Fantasy, Adventure, Drama | S+ | Continuation of an elite modern fantasy adaptation.
Jujutsu Kaisen Season 3 | 2026 | Series | Japan | Action, Supernatural | S | The Culling Game continuation keeps the franchise in the top production tier.
Dorohedoro Season 2 | 2026 | Series | Japan | Dark Fantasy, Action, Comedy | S | The long-awaited return of one of modern anime's weirdest worlds.
CITY THE ANIMATION | 2025 | Series | Japan | Comedy, Slice-of-life | S | Kyoto Animation applies feature-level craft to absurd everyday comedy.
The Fragrant Flower Blooms With Dignity | 2025 | Series | Japan | Romance, Drama, School | S | A sincere romance with enough character momentum to justify the acclaim.
Blue Box | 2024 | Series | Japan | Romance, Sports, Drama | A+ | Sports ambition and romantic progression move together instead of stalling each other.
Kowloon Generic Romance | 2025 | Series | Japan | Romance, Mystery, Sci-Fi | A+ | Adult romance wrapped around an increasingly uncanny identity mystery.
Apocalypse Hotel | 2025 | Series | Japan | Sci-Fi, Comedy, Post-apocalypse | A+ | An original 2025 series with eccentric charm and strong visual identity.
The Darwin Incident | 2026 | Series | Japan | Drama, Thriller, Social Sci-Fi | A+ | A provocative 2026 adaptation with a genuinely unusual premise.
Nippon Sangoku | 2026 | Series | Japan | Political, Drama, Sci-Fi | A+ | A 2026 political sleeper with a very different flavor from standard action anime.
Prism Rondo | 2026 | Series | Japan | Drama, Romance | A+ | One of 2026's better-regarded drama/romance entries.

# --- Romance / drama / slice-of-life that earn their place ---
Horimiya | 2021 | Series | Japan | Romance, Comedy, School | A+ | Fast romantic progression and strong chemistry; very little pointless stalling.
My Dress-Up Darling | 2022 | Series | Japan | Romance, Comedy, Cosplay | A+ | Exceptional character animation and a relationship that actually has energy.
Toradora! | 2008 | Series | Japan | Romance, Comedy, Drama | A+ | A durable rom-com because its conflicts build toward real consequences.
Your Lie in April | 2014 | Series | Japan | Music, Romance, Drama | A+ | Melodramatic, but the performance animation and emotional arc land hard.
Anohana | 2011 | Series | Japan | Drama, Grief, Friendship | A+ | Short enough that its sentimental premise keeps escalating toward a memorable payoff.
Weathering With You | 2019 | Film | Japan | Romance, Fantasy, Drama | A+ | Shinkai spectacle with a more rebellious edge than its premise suggests.
The Garden of Words | 2013 | Film | Japan | Romance, Drama | A | Forty-six minutes of extraordinary visual craft and melancholy.
5 Centimeters per Second | 2007 | Film | Japan | Romance, Drama | A+ | A compact, unsparing story about distance and timing.
Suzume | 2022 | Film | Japan | Fantasy, Adventure, Romance | S | Shinkai turns grief into a fast-moving road adventure with spectacular set pieces.
Voices of a Distant Star | 2002 | Short Film | Japan | Sci-Fi, Romance | A | Tiny runtime, huge sense of distance; foundational early Shinkai.
The Place Promised in Our Early Days | 2004 | Film | Japan | Sci-Fi, Romance, Drama | A | Early Shinkai scale and melancholy with a more overt science-fiction spine.
I Want to Eat Your Pancreas | 2018 | Film | Japan | Drama, Romance | A+ | Directly emotional without wasting its feature runtime.
Josee, the Tiger and the Fish | 2020 | Film | Japan | Romance, Drama | A+ | Polished adult-ish romance with real conflict and a satisfying arc.
Orange | 2016 | Series | Japan | Romance, Drama, Time Travel | A | Emotional time-message premise gives the school drama urgency.
Insomniacs After School | 2023 | Series | Japan | Romance, School, Drama | A+ | Naturalistic romance with purpose, astronomy and actual progression.
Tsuki ga Kirei | 2017 | Series | Japan | Romance, School | A | Quiet but focused first-love story with a real ending.
Bloom Into You | 2018 | Series | Japan | Romance, Drama | A+ | Introspective romance built around identity and expectation rather than stock misunderstandings.
Given | 2019 | Series | Japan | Music, Romance, Drama | A | Compact band drama with genuine grief underneath the romance.
Wotakoi: Love Is Hard for Otaku | 2018 | Series | Japan | Romance, Comedy, Workplace | A | Adult couples, fast setup and relaxed comedy without endless will-they-won't-they.
Lovely Complex | 2007 | Series | Japan | Romance, Comedy | A | Big personality rom-com with strong comic rhythm.
His and Her Circumstances | 1998 | Series | Japan | Romance, Comedy, Drama | S | Hideaki Anno turns a school romance into a formally inventive character study.
Maison Ikkoku | 1986 | Series | Japan | Romance, Comedy, Classic | A+ | Long, but unusually mature by rom-com standards and ultimately rewarding.
Paradise Kiss | 2005 | Series | Japan | Romance, Fashion, Drama | A | Adult consequences and fashion-world energy in a compact run.
Rascal Does Not Dream of Bunny Girl Senpai | 2018 | Series | Japan | Romance, Supernatural, Drama | A+ | Sharp dialogue and supernatural metaphors keep the relationship drama moving.
Kokoro Connect | 2012 | Series | Japan | Supernatural, Drama, Romance | A | Body-swapping and other phenomena force character conflicts into the open.
ReLIFE | 2016 | Series | Japan | Romance, Comedy, Drama | A | Adult regret reframed through school life; finish with the OVAs.
My Love Story!! | 2015 | Series | Japan | Romance, Comedy | A | The relationship starts early, so the comedy can be about being together rather than stalling.
The Dangers in My Heart | 2023 | Series | Japan | Romance, Comedy, Coming-of-age | A+ | Starts awkward, then develops into one of the strongest recent school romances.
Skip and Loafer | 2023 | Series | Japan | School, Comedy, Drama | A+ | Warm character writing with enough social momentum to avoid becoming inert.
My Happy Marriage | 2023 | Series | Japan | Romance, Fantasy, Drama | A | Period romance with supernatural conflict and strong production values.
Recovery of an MMO Junkie | 2017 | Series | Japan | Romance, Comedy, Gaming | A | Adult romance with a concise run and likable leads.
# --- Explicit adult / hentai that still clears the quality bar ---
Mezzo Forte | 2000 | OVA | Japan | Action, Crime, Hentai, Erotic | A+ | A slick Yasuomi Umetsu crime-action OVA whose explicit cut is genuine hentai, but the animation and set pieces are the reason it belongs here.
Words Worth | 1999 | OVA | Japan | Fantasy, Adventure, Hentai | A | Old-school fantasy hentai that actually commits to a continuing war, mystery and adventure plot rather than functioning as disconnected scenes.
Ogenki Clinic | 1992 | OVA | Japan | Comedy, Hentai, Adult | A | Raunchy adult medical comedy with an actual comic premise and deliberately absurd sexual problem-solving.
Fencer of Minerva | 1994 | OVA | Japan | Fantasy, Adventure, Hentai | A | Softcore fantasy adventure with political intrigue, romance and more narrative ambition than the category usually gets.
Daiakuji: The Xena Buster | 2003 | OVA | Japan | Crime, Action, Hentai | A | Plot-heavy adult animation mixing gang warfare, action and an explicit eroge adaptation.
Tomo-chan Is a Girl! | 2023 | Series | Japan | Romance, Comedy | A | One-season rom-com that actually completes its central arc.
Romantic Killer | 2022 | Series | Japan | Romance, Comedy, Parody | A | High-energy anti-romance premise that still develops real characters.
Monthly Girls' Nozaki-kun | 2014 | Series | Japan | Comedy, Romance | A+ | Mostly comedy, but some of the sharpest gag construction in school anime.
Ouran High School Host Club | 2006 | Series | Japan | Comedy, Romance | A+ | Fast, self-aware genre comedy with an unusually strong ensemble.

# --- Music / arts / workplace ---
Beck: Mongolian Chop Squad | 2004 | Series | Japan | Music, Drama, Coming-of-age | A+ | A proper band story about skill, ego and trying to become good enough.
Carole & Tuesday | 2019 | Series | Japan | Music, Sci-Fi, Drama | A | Strong performances and production even when the competition plot wobbles.
Blue Giant | 2023 | Film | Japan | Music, Drama | S | Jazz performance staged like action cinema; one of the best music-anime films.
Pompo: The Cinephile | 2021 | Film | Japan | Filmmaking, Comedy, Drama | A+ | A brisk love letter to editing and filmmaking that understands pacing.
Blue Period | 2021 | Series | Japan | Art, Drama, Coming-of-age | A | Art-school obsession gives the coming-of-age story real stakes.
Ya Boy Kongming! | 2022 | Series | Japan | Music, Comedy | A+ | Historical strategist becomes a music manager; much smarter and more fun than the gimmick sounds.
Kono Oto Tomare! | 2019 | Series | Japan | Music, Drama, School | A | Ensemble music drama with strong competitive payoff.
Kids on the Slope | 2012 | Series | Japan | Music, Drama | S | Jazz, friendship and volatile emotion with Shinichiro Watanabe direction.

# --- Sports / competition ---
The First Slam Dunk | 2022 | Film | Japan | Basketball, Sports, Drama | S+ | Already in the list; retained as one of animation's best sports films.
Slam Dunk | 1993 | Series | Japan | Basketball, Sports, Comedy | S | Classic sports storytelling with a huge final payoff in the manga/film continuum.
Ace of Diamond | 2013 | Series | Japan | Baseball, Sports | A+ | Long-form team competition with a satisfying development curve.
Major | 2004 | Series | Japan | Baseball, Sports, Drama | A | Follows a baseball life across ages rather than a single school tournament.
Hikaru no Go | 2001 | Series | Japan | Board Game, Sports, Supernatural | S | Makes Go feel like a battle series while telling a terrific growth story.
Baby Steps | 2014 | Series | Japan | Tennis, Sports | A | Methodical improvement is the hook; unusually grounded sports progression.
Run with the Wind | 2018 | Series | Japan | Running, Sports, Drama | S | Adult ensemble and one of the genre's best end-runs.
Chihayafuru | 2011 | Series | Japan | Karuta, Sports, Drama | S+ | Poetry card competition somehow becomes ferociously exciting.
Welcome to the Ballroom | 2017 | Series | Japan | Dance, Sports, Drama | A | Competitive dance staged with battle-anime intensity.
Yuri!!! on Ice | 2016 | Series | Japan | Figure Skating, Sports, Romance | A+ | Strong performance sequences and a relationship that matters to the competition arc.
SK8 the Infinity | 2021 | Series | Japan | Skateboarding, Sports | A | Stylish, ridiculous and very easy to binge.
Birdie Wing: Golf Girls' Story | 2022 | Series | Japan | Golf, Sports, Crime | A | Golf treated like underground combat; gloriously absurd.
Ao Ashi | 2022 | Series | Japan | Football, Sports | A+ | Tactical football development with a strong coaching angle.
Tsurune | 2018 | Series | Japan | Archery, Sports, Drama | A | Kyoto Animation makes quiet sports psychology visually compelling.
Uma Musume: Pretty Derby Season 2 | 2021 | Series | Japan | Racing, Sports, Drama | A+ | Ignore the premise; Season 2 is a genuinely excellent sports tragedy.
Medalist | 2025 | Series | Japan | Figure Skating, Sports, Drama | A+ | Strong modern sports drama with excellent emotional stakes.
Orbital Era? | 0 | Series | Japan | Sports | B+ | Placeholder removed during build if unresolved.

# --- Mystery / thriller / psychological ---
Boogiepop Phantom | 2000 | Series | Japan | Psychological, Horror, Mystery | A+ | Fragmented urban horror that rewards attention without overstaying.
Boogiepop and Others | 2019 | Series | Japan | Mystery, Supernatural, Psychological | A | Cleaner modern route into the same strange universe.
Gankutsuou: The Count of Monte Cristo | 2004 | Series | Japan | Revenge, Sci-Fi, Drama | S | Dumas adapted as psychedelic science-fiction revenge opera.
Rainbow | 2010 | Series | Japan | Prison, Drama, Historical | A+ | Brutal postwar survival drama with huge loyalty and revenge payoffs.
Akagi | 2005 | Series | Japan | Gambling, Psychological | A+ | Mahjong becomes pure predatory mind games.
Death Billiards | 2013 | Short Film | Japan | Psychological, Mystery | A | The compact prototype for Death Parade is worth seeing on its own.
Kubikiri Cycle | 2016 | OVA | Japan | Mystery, Dialogue, Murder | A+ | Nisio Isin locked-room mystery with Shaft visual language.
Gosick | 2011 | Series | Japan | Mystery, Historical, Romance | A | Gothic mysteries with a satisfying overarching conspiracy.
The Perfect Insider | 2015 | Series | Japan | Mystery, Locked-room, Psychological | A | Dense locked-room murder mystery aimed at viewers who enjoy deduction.
ACCA: 13-Territory Inspection Dept. | 2017 | Series | Japan | Political, Mystery, Drama | A+ | Low-key coup thriller with adult characters and immaculate atmosphere.
House of Five Leaves | 2010 | Series | Japan | Historical, Crime, Drama | A | Quiet crime drama whose tension comes from character loyalties rather than action.
Migi & Dali | 2023 | Series | Japan | Mystery, Black Comedy | A | Starts absurd and keeps revealing a surprisingly committed mystery.
The Kubikiri Cycle | 2016 | OVA | Japan | Mystery, Psychological | A+ | Duplicate alias handled during build.

# --- Fantasy / adventure / isekai ---
Spice and Wolf: MERCHANT MEETS THE WISE WOLF | 2024 | Series | Japan | Fantasy, Romance, Economics | A+ | Economics, banter and travel with a strong central pair.
Spice and Wolf (2008) | 2008 | Series | Japan | Fantasy, Romance, Economics | A | The original adaptation remains charming even with the newer route available.
The Ancient Magus' Bride | 2017 | Series | Japan | Fantasy, Supernatural, Drama | A+ | Rich folklore and striking atmosphere; slower but continually imaginative.
Ascendance of a Bookworm | 2019 | Series | Japan | Isekai, Fantasy, Politics | A+ | Progression through literacy, craft and social systems instead of raw combat power.
Grimgar of Fantasy and Ash | 2016 | Series | Japan | Isekai, Fantasy, Survival | A | Low-level fantasy survival where death and logistics actually matter.
Log Horizon | 2013 | Series | Japan | Isekai, Strategy, Politics | A+ | MMO isekai focused on systems, governance and group strategy.
Handyman Saitou in Another World | 2023 | Series | Japan | Isekai, Comedy, Adventure | A | Short, funny and unexpectedly sincere ensemble fantasy.
Uncle from Another World | 2022 | Series | Japan | Isekai, Comedy | A+ | Isekai postmortem as aggressively weird Sega-era comedy.
Campfire Cooking in Another World with My Absurd Skill | 2023 | Series | Japan | Isekai, Food, Adventure | A | Relaxed but constantly moving through food, monsters and mercenary logistics.
The Faraway Paladin | 2021 | Series | Japan | Fantasy, Adventure | A | Earnest high-fantasy worldbuilding with a strong first arc.
The Executioner and Her Way of Life | 2022 | Series | Japan | Isekai, Dark Fantasy, Mystery | A | Twists the summoned-hero premise into a murder-and-time mystery.
Reincarnated as a Sword | 2022 | Series | Japan | Isekai, Action, Fantasy | A | Straightforward but unusually likable power-progression duo.
BOFURI | 2020 | Series | Japan | Gaming, Comedy, Fantasy | A | Low-stakes gaming that stays fun because its builds become increasingly ridiculous.
The Wrong Way to Use Healing Magic | 2024 | Series | Japan | Isekai, Action, Comedy | A | Training and combat momentum with a better-than-average ensemble.
Frieren: Beyond Journey's End | 2023 | Series | Japan | Fantasy, Adventure, Drama | S+ | Existing elite pick retained.
Delicious in Dungeon | 2024 | Series | Japan | Fantasy, Adventure, Comedy | S+ | Existing elite pick retained.
Ranking of Kings | 2021 | Series | Japan | Fantasy, Adventure, Drama | S | Existing pick retained.

# --- Comedy ---
The Disastrous Life of Saiki K. | 2016 | Series | Japan | Comedy, Supernatural | S | Machine-gun joke density and one of anime's most reliable comedy ensembles.
Daily Lives of High School Boys | 2012 | Series | Japan | Comedy, School | A+ | Sketch comedy with almost no sentimental padding.
Asobi Asobase | 2018 | Series | Japan | Comedy, School, Absurd | A+ | Violent tonal whiplash and exceptional voice comedy.
Hinamatsuri | 2018 | Series | Japan | Comedy, Supernatural | A+ | Deadpan yakuza/psychic comedy that can suddenly land real emotion.
Cromartie High School | 2003 | Series | Japan | Comedy, Delinquents, Absurd | A | Minimal animation, maximal deadpan absurdity.
Detroit Metal City | 2008 | OVA | Japan | Comedy, Music | A | Short, filthy and extremely committed to its identity crisis joke.
Azumanga Daioh | 2002 | Series | Japan | Comedy, Slice-of-life | A+ | Foundational school comedy with timing that still works.
School Rumble | 2004 | Series | Japan | Comedy, Romance | A | Large-scale romantic farce with energy and escalation.
Sleepy Princess in the Demon Castle | 2020 | Series | Japan | Comedy, Fantasy | A | Turns a kidnapped-princess setup into escalating dungeon vandalism.
Arakawa Under the Bridge | 2010 | Series | Japan | Comedy, Romance, Absurd | A | Shaft oddballs and surreal romantic comedy in equal measure.
Sayonara, Zetsubou-Sensei | 2007 | Series | Japan | Dark Comedy, Satire | A+ | Dense visual satire and wordplay with a singular directorial voice.
Panty & Stocking with Garterbelt | 2010 | Series | Japan | Comedy, Action, Adult | A+ | Gainax vulgarity and Western-cartoon energy animated with total freedom.
New PANTY & STOCKING with GARTERBELT | 2025 | Series | Japan | Comedy, Action, Adult | A | Trigger revival that preserves the original's anarchic appeal.
Pop Team Epic | 2018 | Series | Japan | Comedy, Surreal, Parody | A | Anti-format meme comedy; very uneven by design, but wildly inventive at its peaks.

# --- Horror / supernatural ---
Mononoke | 2007 | Series | Japan | Horror, Mystery, Supernatural | S+ | Formal visual design and psychological mystery unlike anything else on television.
Ayakashi: Samurai Horror Tales | 2006 | Anthology series | Japan | Horror, Folklore | A | The anthology that contains the Medicine Seller arc leading into Mononoke.
School-Live! | 2015 | Series | Japan | Horror, School, Psychological | A | Best entered blind; its cute surface serves a real survival story.
Shadows House | 2021 | Series | Japan | Mystery, Gothic, Supernatural | A | Mansion mystery with distinctive rules and steadily increasing conspiracy.
Ghost Hound | 2007 | Series | Japan | Horror, Psychological, Mystery | A | Slow-burn neurological/supernatural horror with serious atmosphere.
Pet Shop of Horrors | 1999 | OVA | Japan | Horror, Anthology, Supernatural | A | Four concise morality-horror stories with lush 1990s atmosphere.
Hell Girl | 2005 | Series | Japan | Horror, Supernatural, Anthology | A | Repetitive structure, but the best episodes weaponize it effectively.
Vampire Princess Miyu | 1997 | Series | Japan | Horror, Supernatural | A | Melancholy vampire folklore with a strong late-90s mood.
Devilman: The Birth / Demon Bird | 1987 | OVA | Japan | Horror, Action, Classic | A | Ferocious pre-Crybaby Devilman with excellent old-school monster animation.
Angel's Egg | 1985 | Film | Japan | Dark Fantasy, Experimental | S | Minimal dialogue, maximum atmosphere; hypnotic rather than conventionally paced.
Belladonna of Sadness | 1973 | Film | Japan | Experimental, Adult, Drama | S | Psychedelic adult animation with an extraordinary visual identity; very disturbing material.

# --- Sci-fi / cyberpunk / mecha / space ---
Patlabor: The Early Days | 1988 | OVA | Japan | Mecha, Police, Comedy | A+ | The best foundation for the Patlabor films and TV universe.
Patlabor: The TV Series | 1989 | Series | Japan | Mecha, Police, Comedy | A | Workplace mecha with a terrific ensemble.
Mobile Suit Gundam | 1979 | Series | Japan | Mecha, War, Sci-Fi | S+ | Foundational real-robot war drama that still has excellent character stakes.
Mobile Suit Zeta Gundam | 1985 | Series | Japan | Mecha, War, Drama | S | Darker, denser sequel and core Universal Century viewing.
Mobile Suit Gundam ZZ | 1986 | Series | Japan | Mecha, War, Adventure | A | Tonal whiplash early, but important and much stronger once the larger war plot takes over.
Mobile Suit Gundam: The 08th MS Team | 1996 | OVA | Japan | Mecha, War, Romance | A+ | Ground-level mobile-suit warfare with superb OVA production.
Mobile Suit Gundam 0083: Stardust Memory | 1991 | OVA | Japan | Mecha, War, Sci-Fi | A | Gorgeous 90s mecha spectacle despite some character frustration.
Mobile Suit Gundam Hathaway | 2021 | Film | Japan | Mecha, Political Thriller | A+ | Dense political Gundam with outstanding audiovisual design.
Mobile Suit Gundam SEED | 2002 | Series | Japan | Mecha, War, Drama | A | Melodramatic but highly bingeable alternate-universe Gundam.
Mobile Fighter G Gundam | 1994 | Series | Japan | Mecha, Tournament, Action | A | Gundam as giant-robot martial arts tournament; knowingly excessive.
After War Gundam X | 1996 | Series | Japan | Mecha, Post-apocalypse | A | Underrated standalone Gundam with a likable lead pair.
Gundam Build Fighters | 2013 | Series | Japan | Mecha, Tournament, Hobby | A+ | Fanservice in the good sense: inventive model-kit battles with real sports momentum.
Macross | 1982 | Series | Japan | Mecha, Music, Space Opera | S | Foundational transforming-fighter space opera with music central to the plot.
Macross Frontier | 2008 | Series | Japan | Mecha, Music, Space Opera | A+ | Polished modern Macross with huge musical set pieces.
Macross: Do You Remember Love? | 1984 | Film | Japan | Mecha, Music, Romance | S | Feature-film reconstruction of Macross with staggering hand-drawn spectacle.
Martian Successor Nadesico | 1996 | Series | Japan | Mecha, Comedy, Sci-Fi | A | Genre-savvy mecha comedy that develops genuine wartime stakes.
The Big O | 1999 | Series | Japan | Mecha, Noir, Mystery | A+ | Batman-meets-super-robot noir with a unique art-deco identity.
GaoGaiGar | 1997 | Series | Japan | Super Robot, Action | A | The super-robot genre at maximum sincerity and escalating spectacle.
Diebuster | 2004 | OVA | Japan | Mecha, Sci-Fi, Drama | A+ | Hyperactive sequel/companion to Gunbuster with a huge emotional finish.
Knights of Sidonia | 2014 | Series | Japan | Space, Mecha, Survival | A | CG takes adjustment, but the claustrophobic space-survival story works.
The Orbital Children | 2022 | ONA | Japan | Sci-Fi, Space, AI | A+ | Dense six-episode near-future space disaster from Mitsuo Iso.
Last Exile | 2003 | Series | Japan | Steampunk, Adventure, War | A+ | Airship adventure with a distinctive world and Gonzo at its best.
Noein | 2005 | Series | Japan | Sci-Fi, Parallel Worlds, Drama | A | Quantum multiverse ideas with excellent experimental action animation.
Dennou Coil | 2007 | Series | Japan | Augmented Reality, Mystery | S | Childhood adventure that becomes serious speculative fiction.
Serial Experiments Lain | 1998 | Series | Japan | Cyberpunk, Psychological | S | Existing pick retained and elevated as a cyberculture landmark.
Texhnolyze | 2003 | Series | Japan | Cyberpunk, Psychological, Dark | A+ | Extremely bleak and slow, but formally committed and rewarding if you want uncompromising cyberpunk.
Ergo Proxy | 2006 | Series | Japan | Cyberpunk, Mystery, Philosophy | A+ | Existing pick retained.
Ghost in the Shell 2: Innocence | 2004 | Film | Japan | Cyberpunk, Crime, Philosophy | A+ | Dense philosophical sequel with extraordinary digital/hand-drawn craft.
Ghost in the Shell: Stand Alone Complex 2nd GIG | 2004 | Series | Japan | Cyberpunk, Politics, Crime | S+ | One of the strongest seasons of political cyberpunk television.
Psycho-Pass 3 | 2019 | Series | Japan | Cyberpunk, Crime, Thriller | A | Later-continuity entry that recovers some of the procedural complexity.
Akudama Drive | 2020 | Series | Japan | Cyberpunk, Crime, Action | A+ | Existing pick retained.
Vivy: Fluorite Eye's Song | 2021 | Series | Japan | AI, Time Travel, Action | A+ | Existing pick retained.
Expelled from Paradise | 2014 | Film | Japan | Sci-Fi, Mecha, Action | A | Early CG feature that succeeds on design, ideas and a strong final battle.
Genocidal Organ | 2017 | Film | Japan | Sci-Fi, War, Thriller | A | Grim geopolitical science fiction from Project Itoh.
Harmony | 2015 | Film | Japan | Sci-Fi, Dystopia, Psychological | A | Clinical utopia turned philosophical thriller.
The Empire of Corpses | 2015 | Film | Japan | Steampunk, Adventure, Horror | A | Messy but visually ambitious Project Itoh adventure worth it for the world.
Sky Crawlers | 2008 | Film | Japan | War, Sci-Fi, Drama | A+ | Mamoru Oshii aerial combat as existential repetition.
Royal Space Force: The Wings of Honnêamise | 1987 | Film | Japan | Sci-Fi, Drama | S | Lavish alternate-world space-race film and Gainax landmark.
Robot Carnival | 1987 | Anthology film | Japan | Sci-Fi, Anthology, Animation | A+ | Showcase anthology from major 1980s animators.
Neo Tokyo | 1987 | Anthology film | Japan | Sci-Fi, Horror, Anthology | A | Three highly distinctive shorts from Rintaro, Kawajiri and Otomo.
Short Peace | 2013 | Anthology film | Japan | Anthology, Historical, Sci-Fi | A | Otomo-linked anthology with superb craft.
Genius Party | 2007 | Anthology film | Japan | Experimental, Anthology | A | Studio 4°C animator showcase with wildly different visual ideas.
Genius Party Beyond | 2008 | Anthology film | Japan | Experimental, Anthology | A | Companion anthology with equally adventurous shorts.

# --- Action / adventure / historical ---
Samurai X: Reflection | 2001 | OVA | Japan | Historical, Drama, Samurai | A | Divisive canon status, but visually beautiful as a tragic alternate coda.
Sword of the Stranger | 2007 | Film | Japan | Samurai, Action | S | Existing pick retained; one of the cleanest action-film recommendations.
Vampire Hunter D | 1985 | OVA | Japan | Horror, Action, Vampire | A | Rougher than Bloodlust but an essential gothic 80s OVA.
Demon City Shinjuku | 1988 | OVA | Japan | Horror, Action, Supernatural | A | Kawajiri pulp horror with great atmosphere and creature work.
Cyberpunk: Edgerunners | 2022 | Series | Japan / Poland | Cyberpunk, Action, Drama | S+ | Existing elite pick retained.
Lupin the Third: The Woman Called Fujiko Mine | 2012 | Series | Japan | Crime, Adult, Adventure | S | Stylish adult reinterpretation with Sayo Yamamoto direction.
Lupin III Part II | 1977 | Series | Japan | Crime, Comedy, Adventure | A+ | Classic episodic Lupin with an enormous supply of great capers.
Lupin the Third: Part 5 | 2018 | Series | Japan | Crime, Adventure, Technology | A+ | Modern Lupin that understands both the character and the internet age.
City Hunter | 1987 | Series | Japan | Action, Comedy, Crime | A | Very 80s, very long, but charismatic urban action-comedy at its best.
Dirty Pair | 1985 | Series | Japan | Sci-Fi, Action, Comedy | A+ | Space-action buddy comedy with excellent 80s design and animation.
Black Jack OVA | 1993 | OVA | Japan | Medical, Drama, Thriller | A+ | Osamu Dezaki turns medical cases into operatic adult drama.
Golgo 13: The Professional | 1983 | Film | Japan | Crime, Action, Adult | A | Cold-blooded assassin pulp with legendary Dezaki style.
Golgo 13 | 2008 | Series | Japan | Crime, Action, Adult | A | Straightforward adult assassin procedurals.
Golgo 13: Queen Bee | 1998 | OVA | Japan | Crime, Action, Adult | A | Compact Dezaki/Golgo pulp.
Golden Kamuy | 2018 | Series | Japan | Historical, Adventure, Comedy | S | Existing pick retained.
Kingdom | 2012 | Series | Japan | Historical, War, Strategy | A+ | Ugly early CG gives way to an enormous, addictive war epic.
Yona of the Dawn | 2014 | Series | Japan | Fantasy, Adventure, Romance | A+ | Strong heroine-growth adventure that ends far too early but is worth the season.
The Heroic Legend of Arslan | 2015 | Series | Japan | Historical Fantasy, War | A | Straightforward kingdom-reclamation epic with good strategic momentum.
Vinland Saga | 2019 | Series | Japan | Historical, Drama, Action | S+ | Existing elite pick retained.
Dororo | 2019 | Series | Japan | Historical, Dark Fantasy | A+ | Existing pick retained.
Blade of the Immortal (2019) | 2019 | Series | Japan | Samurai, Revenge | A+ | Existing pick retained.
Revenger | 2023 | Series | Japan | Historical, Action, Crime | A | Stylish assassination drama with a complete one-season arc.
Sword of the Demon Hunter: Kijin Gentosho | 2025 | Series | Japan | Historical, Fantasy, Action | A | Long-timespan demon tale with an appealing historical-fantasy hook.
Elusive Samurai | 2024 | Series | Japan | Historical, Action | A+ | Visually playful historical action from CloverWorks.

# --- Shonen / mainstream / adventure extras ---
Dragon Ball | 1986 | Series | Japan | Action, Adventure, Comedy | S | The adventure/comedy beginning is essential context before Z if you want the full journey.
Dragon Ball Super | 2015 | Series | Japan | Action, Martial Arts | A | Uneven television production, but several arcs and Tournament of Power deliver huge franchise highs.
Dragon Ball Super: Broly | 2018 | Film | Japan | Action, Martial Arts | S | One of the franchise's best animated fights and the cleanest modern DB movie.
Dragon Ball Super: Super Hero | 2022 | Film | Japan | Action, Superhero, Comedy | A+ | CG experiment with strong Piccolo/Gohan character focus.
Hunter x Hunter (1999) | 1999 | Series | Japan | Adventure, Action | A | A moodier alternate adaptation with a particularly strong Yorknew presentation.
Fullmetal Alchemist (2003) | 2003 | Series | Japan | Fantasy, Adventure, Drama | S | Not a failed Brotherhood draft: a genuinely different, darker interpretation worth seeing separately.
Fullmetal Alchemist the Movie: Conqueror of Shamballa | 2005 | Film | Japan | Fantasy, Adventure | A | The direct ending route for the 2003 continuity.
Bleach: Thousand-Year Blood War | 2022 | Series | Japan | Action, Supernatural | S | Modern production upgrade that turns late Bleach into premium spectacle.
Naruto | 2002 | Series | Japan | Action, Ninja, Adventure | A+ | The original run's best arcs remain genre-defining; use a filler guide.
Naruto Shippuden | 2007 | Series | Japan | Action, Ninja, War | A | Massive highs and massive filler; the guide makes it manageable.
One Piece Fan Letter | 2024 | Special | Japan | Adventure, Drama | S | A beautiful short celebration of One Piece from ordinary people's perspective.
Dragon Quest: The Adventure of Dai | 2020 | Series | Japan | Fantasy, Adventure, Action | A+ | Complete modern shonen adaptation with classic pacing done right.
World Trigger | 2014 | Series | Japan | Action, Strategy, Sci-Fi | A+ | Rough early production, but some of shonen's best tactical team combat.
D.Gray-man | 2006 | Series | Japan | Dark Fantasy, Action | A | Gothic long-form shonen with strong atmosphere and villains.
Kekkaishi | 2006 | Series | Japan | Supernatural, Action | A | Underseen battle shonen with smart barrier powers and solid progression.
Blue Exorcist | 2011 | Series | Japan | Supernatural, Action | A | Franchise continuity is messy, but the better arcs are worth navigating.
Black Clover | 2017 | Series | Japan | Fantasy, Action | A | Starts loud and rough, then becomes extremely bingeable team-battle shonen.
Magi: The Kingdom of Magic | 2013 | Series | Japan | Fantasy, Adventure, Politics | A+ | Stronger second season deepens the franchise's politics and worldbuilding.
Magi: Adventure of Sinbad | 2016 | Series | Japan | Fantasy, Adventure | A | Charismatic prequel route.
Zatch Bell! | 2003 | Series | Japan | Action, Comedy, Supernatural | A | Old-school battle anime with a surprisingly emotional tournament core.
Shaman King (2001) | 2001 | Series | Japan | Supernatural, Action | A | Older adaptation has atmosphere and personality even though it diverges.
Law of Ueki | 2005 | Series | Japan | Action, Comedy, Tournament | A | Creative powers and an underrated complete battle-tournament story.
Ushio and Tora | 2015 | Series | Japan | Supernatural, Action, Adventure | A+ | Old-school yokai shonen compressed into a vigorous modern adaptation.
Karakuri Circus | 2018 | Series | Japan | Action, Drama, Supernatural | A | Overcompressed, but enormous melodramatic invention and momentum.
Rage of Bahamut: Genesis | 2014 | Series | Japan | Fantasy, Adventure, Action | A+ | Swashbuckling fantasy with movie-like direction and charismatic leads.

# --- Classic / influential television ---
Astro Boy (1963) | 1963 | Series | Japan | Sci-Fi, Adventure, Classic | B+ | Historically foundational; included as a classic rather than a first recommendation.
Space Battleship Yamato | 1974 | Series | Japan | Space Opera, War, Classic | A | Foundational serialized anime space opera.
Galaxy Express 999 | 1978 | Series | Japan | Space Opera, Adventure, Classic | A | Leiji Matsumoto's melancholy cosmic travelogue.
Captain Harlock | 1978 | Series | Japan | Space Opera, Adventure | A | Romantic space-pirate mythmaking with iconic design.
The Ideon | 1980 | Series | Japan | Mecha, Sci-Fi, War | A | Tomino despair gradually becomes cosmic catastrophe; End of Ideon is essential.
The Ideon: Be Invoked | 1982 | Film | Japan | Mecha, Sci-Fi, Apocalypse | S | One of the most extreme endings in classic mecha.
Urusei Yatsura (1981) | 1981 | Series | Japan | Comedy, Romance, Sci-Fi | A | Massive, influential comedy with many standout Oshii-era episodes.
Urusei Yatsura 2: Beautiful Dreamer | 1984 | Film | Japan | Comedy, Surreal, Sci-Fi | S | Mamoru Oshii transforms a gag franchise into an existential dream film.
Maison Ikkoku | 1986 | Series | Japan | Romance, Comedy, Classic | A+ | Long-form adult-ish romance with an actual finish.
Ranma 1/2 (1989) | 1989 | Series | Japan | Comedy, Martial Arts, Romance | A | Iconic gender-bending martial-arts farce; episodic but endlessly energetic at its best.
Ranma 1/2 (2024) | 2024 | Series | Japan | Comedy, Martial Arts, Romance | A+ | Clean modern production without losing Takahashi's comic speed.
Fist of the North Star | 1984 | Series | Japan | Action, Martial Arts, Post-apocalypse | A | Repetitive but iconic and emotionally operatic at its peaks.
Saint Seiya | 1986 | Series | Japan | Action, Mythology | A | Mythic armor battles and melodrama that defined a generation internationally.
Sailor Moon | 1992 | Series | Japan | Magical Girl, Adventure, Romance | A+ | Foundational magical-girl team adventure; use curated episode guidance if the length intimidates.
Cardcaptor Sakura | 1998 | Series | Japan | Magical Girl, Fantasy, Romance | S | Elegant episodic structure, lovable characters and exceptional Madhouse craft.
Magic Knight Rayearth | 1994 | Series | Japan | Fantasy, Mecha, Magical Girl | A | CLAMP fantasy adventure with a memorable late twist.
Slayers | 1995 | Series | Japan | Fantasy, Comedy, Adventure | A+ | Fast sword-and-sorcery comedy with a charismatic cast.
Now and Then, Here and There | 1999 | Series | Japan | Isekai, War, Drama | A+ | Brutal anti-war isekai from long before the modern power-fantasy wave.
Infinite Ryvius | 1999 | Series | Japan | Sci-Fi, Survival, Drama | A | Lord-of-the-Flies-in-space social collapse with a huge teen ensemble.
Record of Lodoss War | 1990 | OVA | Japan | Fantasy, Adventure | A | Pure high-fantasy OVA atmosphere and iconic 90s art.
Bubblegum Crisis | 1987 | OVA | Japan | Cyberpunk, Action, Music | A+ | Neon powered-armor cyberpunk with some of the era's best OVA style.
Megazone 23 | 1985 | OVA | Japan | Cyberpunk, Mecha, Mystery | A | Pop-idol mecha conspiracy that anticipated later virtual-reality anime.
Area 88 | 1985 | OVA | Japan | War, Aviation, Drama | A+ | Excellent aerial combat wrapped around a mercenary tragedy.
Black Magic M-66 | 1987 | OVA | Japan | Sci-Fi, Action | A | Short Shirow military-android chase with exceptional mechanical animation.
Crusher Joe | 1983 | Film | Japan | Space Opera, Adventure | A | Gorgeous old-school space adventure with relentless movement.
Space Adventure Cobra | 1982 | Series | Japan | Space Opera, Action | A | Pulp space adventure with charisma to spare.

# --- Modern genre standouts ---
Beastars | 2019 | Series | Japan | Drama, Mystery, Romance | A+ | Social predator/prey metaphor becomes a surprisingly tense character thriller.
Land of the Lustrous | 2017 | Series | Japan | Fantasy, Mystery, CG | S | Existing pick retained; one of CG anime's clearest aesthetic breakthroughs.
To Your Eternity | 2021 | Series | Japan | Fantasy, Drama, Adventure | A+ | Built to hurt, but the immortality premise keeps reinventing the stakes.
Sonny Boy | 2021 | Series | Japan | Sci-Fi, Surreal, Coming-of-age | S | Abstract but concise, with exceptional direction and music.
Heike Monogatari | 2021 | Series | Japan | Historical, Drama | S | Naoko Yamada turns classical history into intimate tragedy.
The Eccentric Family | 2013 | Series | Japan | Fantasy, Comedy, Family | A+ | Kyoto folklore, family politics and wit with real melancholy underneath.
Kyousougiga | 2013 | Series | Japan | Fantasy, Family, Surreal | A+ | Hyperactive visual imagination wrapped around a surprisingly coherent family myth.
Flip Flappers | 2016 | Series | Japan | Magical Girl, Adventure, Surreal | A | Constantly changing visual worlds and high-end animation.
Little Witch Academia | 2017 | Series | Japan | Fantasy, Comedy, Adventure | A+ | Trigger charm and expressive animation in a relentlessly likable magic-school adventure.
SSSS.GRIDMAN | 2018 | Series | Japan | Tokusatsu, Mecha, Mystery | A+ | Starts as monster-of-the-week homage and reveals a much sharper emotional structure.
SSSS.DYNAZENON | 2021 | Series | Japan | Tokusatsu, Mecha, Drama | A+ | More grounded character drama inside Trigger's tokusatsu framework.
Gridman Universe | 2023 | Film | Japan | Tokusatsu, Mecha, Romance | A+ | Franchise-crossover payoff that actually lands the character arcs.
BNA: Brand New Animal | 2020 | Series | Japan | Action, Fantasy, Sci-Fi | A | Uneven ending, but energetic Trigger design and action make it worthwhile.
Little Witch Academia: The Enchanted Parade | 2015 | Short Film | Japan | Fantasy, Comedy | A | Excellent compact Trigger showcase.
Revue Starlight | 2018 | Series | Japan | Music, Drama, Surreal | A+ | Stage competition becomes symbolic sword duels with outstanding direction.
Revue Starlight: The Movie | 2021 | Film | Japan | Music, Drama, Surreal | S | A maximalist sequel film that pushes the series' visual language much further.
Princess Principal | 2017 | Series | Japan | Spy, Steampunk, Action | A+ | Nonlinear spy missions with strong atmosphere and a great ensemble.
Akiba Maid War | 2022 | Series | Japan | Crime, Comedy, Action | A+ | Maid cafes treated as yakuza turf wars; commits completely to the bit.
Buddy Daddies | 2023 | Series | Japan | Action, Comedy, Family | A | Assassins raising a child, but with enough action and character growth to stay lively.
Maquia: When the Promised Flower Blooms | 2018 | Film | Japan | Fantasy, Drama, Family | S | A fantasy motherhood story with a huge emotional time horizon.
The Aquatope on White Sand | 2021 | Series | Japan | Workplace, Drama | A | Aquarium workplace drama with visual polish and clear character progression.
Nagi-Asu: A Lull in the Sea | 2013 | Series | Japan | Fantasy, Romance, Drama | A+ | Beautiful worldbuilding and a relationship web that actually evolves.
Angel Beats! | 2010 | Series | Japan | Supernatural, Drama, Comedy | A | Messy but compact and emotionally effective.
Charlotte | 2015 | Series | Japan | Supernatural, Drama | A | Rushed late stretch, but enough big turns and strong production to remain entertaining.

# --- Directors / films / animation landmarks ---
Mind Game | 2004 | Film | Japan | Experimental, Comedy, Adventure | S | Masaaki Yuasa's feature-length declaration of visual freedom.
The Night Is Short, Walk on Girl | 2017 | Film | Japan | Comedy, Romance, Surreal | S | Tatami-universe nightlife compressed into one dizzy, joyous movie.
Inu-Oh | 2021 | Film | Japan | Historical, Music, Fantasy | S | Medieval rock opera by Masaaki Yuasa with extraordinary performance sequences.
Lu Over the Wall | 2017 | Film | Japan | Fantasy, Music, Comedy | A+ | Yuasa mermaid chaos with some astonishingly loose animation.
Ride Your Wave | 2019 | Film | Japan | Romance, Fantasy, Drama | A | Sincere grief romance with Yuasa's fluid visual touch.
The Colors Within | 2024 | Film | Japan | Music, Drama, Coming-of-age | S | Naoko Yamada's gentle musical filmmaking is precise rather than inert.
Tamako Love Story | 2014 | Film | Japan | Romance, Coming-of-age | A+ | Turns a light TV comedy into a beautifully observed, decisive romance.
Colorful | 2010 | Film | Japan | Drama, Supernatural | A+ | Reincarnation premise becomes a focused adolescent moral drama.
The Anthem of the Heart | 2015 | Film | Japan | Drama, Music, Romance | A | Emotionally direct youth drama built around performance.
Summer Ghost | 2021 | Short Film | Japan | Drama, Supernatural | A | Forty minutes, strong atmosphere and no wasted setup.
Penguin Highway | 2018 | Film | Japan | Sci-Fi, Coming-of-age, Mystery | A+ | Childlike curiosity meets genuinely strange science-fiction.
Patema Inverted | 2013 | Film | Japan | Sci-Fi, Adventure, Romance | A | Clever gravity gimmick produces real visual adventure.
The Case of Hana & Alice | 2015 | Film | Japan | Mystery, Comedy, Coming-of-age | A+ | Rotoscoped school mystery with unusually natural motion and dialogue.
Miss Hokusai | 2015 | Film | Japan | Historical, Art, Drama | A | Episodic portrait of an artist with gorgeous Edo atmosphere.
Mai Mai Miracle | 2009 | Film | Japan | Coming-of-age, Drama | A | Childhood imagination and postwar change without cloying sentimentality.
Giovanni's Island | 2014 | Film | Japan | Historical, Drama | A | Postwar displacement seen through children, with strong visual storytelling.
Barefoot Gen | 1983 | Film | Japan | War, Drama | A+ | Harrowing Hiroshima film with blunt, unforgettable imagery.
Night on the Galactic Railroad | 1985 | Film | Japan | Fantasy, Drama, Surreal | A+ | Dreamlike literary adaptation with enormous melancholy atmosphere.

# --- Studio Ghibli complete official works collection (27 works) ---
The Boy and the Heron | 2023 | Film | Japan | Fantasy, Adventure, Drama | S | Miyazaki's dense late-career dream journey.
Earwig and the Witch | 2020 | Film | Japan | Fantasy, Family, CG | B | Included to make the official Studio Ghibli collection complete; not one of the studio's strongest.
The Red Turtle | 2016 | Film | France / Japan | Drama, Fantasy, Dialogue-free | A+ | Minimal dialogue and elegant visual storytelling in a Ghibli co-production.
When Marnie Was There | 2014 | Film | Japan | Drama, Mystery | A+ | Intimate mystery with beautiful atmosphere and a strong emotional reveal.
The Wind Rises | 2013 | Film | Japan | Historical, Drama, Romance | S | Ambitious, conflicted biography-fantasia about creation and consequence.
From Up on Poppy Hill | 2011 | Film | Japan | Romance, Historical, Drama | A | Brisk period romance with a great sense of place.
Arrietty | 2010 | Film | Japan | Fantasy, Adventure | A+ | Tiny-scale adventure with exquisite environmental detail.
Ponyo | 2008 | Film | Japan | Fantasy, Adventure, Family | A+ | Hand-drawn elemental chaos disguised as a children's fairy tale.
Tales from Earthsea | 2006 | Film | Japan | Fantasy, Adventure | B | Included for complete Ghibli coverage; visually strong but narratively uneven.
Howl's Moving Castle | 2004 | Film | Japan | Fantasy, Romance, Adventure | S | Maximal Miyazaki fantasy, war anxiety and one of animation's great moving structures.
The Cat Returns | 2002 | Film | Japan | Fantasy, Adventure, Comedy | A | Short, breezy Ghibli fantasy with no bloat.
Ghiblies Episode 2 | 2002 | Short Film | Japan | Comedy, Slice-of-life | B+ | Official Ghibli short included for collection completeness.
My Neighbors the Yamadas | 1999 | Film | Japan | Comedy, Family | A+ | Takahata's loose watercolor family comedy is formally radical and often hilarious.
Whisper of the Heart | 1995 | Film | Japan | Romance, Coming-of-age | S | Creative ambition and first love with one of Ghibli's most grounded emotional arcs.
On Your Mark | 1995 | Music Video | Japan | Sci-Fi, Adventure | A | Six-minute Miyazaki sci-fi music video; tiny but visually rich.
Pom Poko | 1994 | Film | Japan | Fantasy, Comedy, Environmental | A+ | Ecological war comedy that gets much stranger and sadder than its premise suggests.
Ocean Waves | 1993 | TV Film | Japan | Romance, Drama | B+ | Minor Ghibli, but a concise and interesting youth drama.
Porco Rosso | 1992 | Film | Japan | Adventure, Romance, Aviation | S | Wry adult Miyazaki adventure with gorgeous aircraft animation.
Only Yesterday | 1991 | Film | Japan | Drama, Memory, Romance | S | Adult memory drama whose visual transitions make introspection cinematic.
Kiki's Delivery Service | 1989 | Film | Japan | Fantasy, Coming-of-age | S+ | Effortless character storytelling about work, confidence and burnout.
My Neighbor Totoro | 1988 | Film | Japan | Fantasy, Family, Adventure | S+ | Gentle but never empty; visual storytelling and atmosphere are nearly perfect.
Castle in the Sky | 1986 | Film | Japan | Adventure, Fantasy, Sci-Fi | S+ | Pure adventure cinema with robots, air pirates and relentless movement.

# --- Other acclaimed anime films ---
Look Back | 2024 | Film | Japan | Drama, Art, Coming-of-age | S+ | Compact, beautifully animated story about friendship, art and grief.
100 Meters | 2025 | Film | Japan | Sports, Drama | S | 2026 Anime Awards film nominee with a distinctive approach to running and obsession.
Chainsaw Man - The Movie: Reze Arc | 2025 | Film | Japan | Action, Romance, Horror | S+ | Major Chainsaw Man continuation and one of the most acclaimed 2025 anime films.
Demon Slayer: Kimetsu no Yaiba Infinity Castle | 2025 | Film | Japan | Action, Dark Fantasy | S | 2026 Anime Awards Film of the Year winner and franchise spectacle at maximum scale.
Mononoke the Movie: Phantom in the Rain | 2024 | Film | Japan | Horror, Mystery, Supernatural | A+ | The Medicine Seller returns in a visually extravagant new film continuity.
Mononoke the Movie: Chapter II - The Ashes of Rage | 2025 | Film | Japan | Horror, Mystery, Supernatural | S | 2026 awards-level continuation of the Mononoke film project.
The Rose of Versailles (2025) | 2025 | Film | Japan | Historical, Drama, Romance | A+ | Modern feature reimagining of the classic shoujo epic.
Scarlet | 2025 | Film | Japan | Fantasy, Drama | A+ | Mamoru Hosoda's latest feature and a 2026 Anime Awards film nominee.
Belle | 2021 | Film | Japan | Sci-Fi, Music, Drama | A+ | Hosoda digital-world spectacle with huge musical sequences.
Summer Wars | 2009 | Film | Japan | Sci-Fi, Family, Adventure | S | Digital crisis, family comedy and action all move with feature-film efficiency.
The Boy and the Beast | 2015 | Film | Japan | Fantasy, Action, Coming-of-age | A+ | Martial-arts fantasy with a strong surrogate-family arc.
Mirai | 2018 | Film | Japan | Fantasy, Family, Coming-of-age | A | Small-scale family fantasy with exceptional visual observation.
Paprika | 2006 | Film | Japan | Sci-Fi, Psychological, Surreal | S+ | Existing pick retained and elevated.
Tekkonkinkreet | 2006 | Film | Japan | Crime, Fantasy, Drama | S | Existing pick retained; Studio 4°C at full visual power.
Children of the Sea | 2019 | Film | Japan | Mystery, Ocean, Experimental | A+ | Narrative is elusive, but the audiovisual ocean spectacle is extraordinary.
Mutafukaz | 2017 | Film | France / Japan | Action, Crime, Sci-Fi | A | Studio 4°C urban action co-production with a distinctive comic-book pulse.
Berserk: The Golden Age Arc - Memorial Edition | 2022 | Series | Japan | Dark Fantasy, War, Drama | A+ | Best animated condensed alternative to 1997 for the Golden Age story.

# --- Western / international anime-adjacent and stylized animation ---
Spider-Man: Into the Spider-Verse | 2018 | Western film | US | Superhero, Action, Coming-of-age | S+ | A modern animation landmark whose comic/anime-influenced language changed mainstream features.
Spider-Man: Across the Spider-Verse | 2023 | Western film | US | Superhero, Action, Multiverse | S+ | Even more formally ambitious than the first film, with astonishing visual world design.
KPop Demon Hunters | 2025 | Western film | US / South Korea | Music, Action, Fantasy | S | Pop-musical action animation with obvious anime influence and exceptional mainstream craft.
The Mitchells vs. the Machines | 2021 | Western film | US | Comedy, Sci-Fi, Family | S | Spider-Verse-era graphic animation language applied to a genuinely funny robot apocalypse.
Puss in Boots: The Last Wish | 2022 | Western film | US | Fantasy, Adventure, Action | S | Painterly action staging and anime-influenced timing elevate a sequel nobody expected to be this good.
Teenage Mutant Ninja Turtles: Mutant Mayhem | 2023 | Western film | US | Action, Comedy, Coming-of-age | A+ | Scribbled comic-book texture and fast character comedy with strong animation identity.
Nimona | 2023 | Western film | US | Fantasy, Sci-Fi, Adventure | A+ | Fast, funny shapeshifter adventure with a strong emotional core.
Entergalactic | 2022 | Western film | US | Romance, Music, Adult | A | Stylish adult romance whose animation owes plenty to the post-Spider-Verse wave.
Avatar: The Last Airbender | 2005 | Western series | US / South Korea | Fantasy, Adventure, Action | S+ | Existing pick retained and elevated as a complete animated epic.
The Legend of Korra | 2012 | Western series | US / South Korea | Fantasy, Action, Politics | S | Messier than Avatar but frequently more ambitious and visually spectacular.
The Boondocks | 2005 | Western series | US / South Korea | Satire, Comedy, Action | A+ | Anime-influenced staging applied to vicious American social satire.
Teen Titans | 2003 | Western series | US | Superhero, Action, Comedy | A+ | One of the clearest pre-streaming American anime-influenced action series.
Rise of the Teenage Mutant Ninja Turtles | 2018 | Western series | US | Action, Comedy | A | Hyperkinetic anime-influenced action animation; the movie is the peak.
Rise of the Teenage Mutant Ninja Turtles: The Movie | 2022 | Western film | US | Action, Sci-Fi, Comedy | A+ | Feature-length payoff with absurdly good action animation.
My Adventures with Superman | 2023 | Western series | US / South Korea | Superhero, Romance, Action | A | Bright anime-informed Superman with a fast-moving cast dynamic.
Voltron: Legendary Defender | 2016 | Western series | US / South Korea | Mecha, Adventure, Sci-Fi | A | Studio Mir action and strong early seasons; later plotting is more divisive.
Pantheon | 2022 | Western series | US | Sci-Fi, AI, Thriller | S+ | Existing pick retained; one of Western adult animation's best science-fiction stories.
Scavengers Reign | 2023 | Western series | US | Sci-Fi, Survival, Ecological | S+ | Existing pick retained; alien ecology as visual storytelling.
Invincible | 2021 | Western series | US | Superhero, Drama, Gore | S | Existing pick retained; character stakes matter as much as the brutality.
Primal | 2019 | Western series | US | Survival, Action, Prehistoric | S+ | Existing pick retained; near-wordless visual storytelling at an elite level.
Arcane | 2021 | Western series | France / US | Fantasy, Drama, Action | S+ | Existing elite pick retained; one of the visual benchmarks for streaming animation.
Blue Eye Samurai | 2023 | Western series | US / France | Historical, Revenge, Action | S+ | Existing elite pick retained.
Love, Death + Robots | 2019 | Western anthology | International | Sci-Fi, Horror, Anthology | S | Existing pick retained; uneven by design but essential as an adult-animation showcase.
The Animatrix | 2003 | Western anthology | US / Japan | Sci-Fi, Cyberpunk, Anthology | S | Existing pick retained and a key bridge between Hollywood and anime studios.
Star Wars: Visions | 2021 | Western anthology | International | Sci-Fi, Anthology, Action | A+ | Existing pick retained; studio-by-studio freedom produces several exceptional shorts.
The Ninth Jedi | 2026 | Western series | Japan / US | Sci-Fi, Action, Star Wars | A+ | Expanded Star Wars: Visions concept with direct anime pedigree.
Castlevania | 2017 | Western series | US | Dark Fantasy, Action, Horror | S | Existing pick retained.
Castlevania: Nocturne | 2023 | Western series | US | Dark Fantasy, Action, Horror | A+ | Existing pick retained.
Devil May Cry (2025) | 2025 | Western series | US / South Korea | Action, Demons, Comedy | A+ | Existing pick retained.
Splinter Cell: Deathwatch | 2025 | Western series | US / France | Espionage, Action, Thriller | A+ | Existing pick retained.
Tomb Raider: The Legend of Lara Croft | 2024 | Western series | US | Adventure, Action | A | Existing pick retained.
The Legend of Vox Machina | 2022 | Western series | US | Fantasy, Action, Comedy | A+ | Existing pick retained.
The Mighty Nein | 2025 | Western series | US | Fantasy, Adventure, Adult | A | Companion Critical Role adaptation with a darker ensemble flavor.
Blood of Zeus | 2020 | Western series | US | Mythology, Action, Dark Fantasy | A | Existing pick retained.
Twilight of the Gods | 2024 | Western series | US / France | Mythology, Revenge, Adult | A | Existing pick retained.
Trese | 2021 | Western series | Philippines / US | Horror, Crime, Folklore | A | Existing pick retained.
Seis Manos | 2019 | Western series | US | Martial Arts, Horror, Crime | A | Existing pick retained.
DOTA: Dragon's Blood | 2021 | Western series | US / South Korea | Fantasy, Action | A | Messy compression, but strong Studio Mir action and dark fantasy momentum.
The Witcher: Nightmare of the Wolf | 2021 | Western film | US / South Korea | Fantasy, Action, Horror | A+ | Studio Mir turns Witcher lore into clean adult action animation.
Dragon Age: Absolution | 2022 | Western series | US / South Korea | Fantasy, Action | A | Compact video-game adaptation with strong ensemble action.
Captain Laserhawk: A Blood Dragon Remix | 2023 | Western series | France | Cyberpunk, Action, Satire | A | Maximal Ubisoft remix with a surprising political streak.
Common Side Effects | 2025 | Western series | US | Thriller, Comedy, Adult | A+ | Not especially anime-looking, but one of the strongest recent adult animated thrillers.
Aeon Flux | 1991 | Western series | US | Sci-Fi, Action, Experimental | A+ | Adult animation landmark with a visual grammar closer to avant-garde anime than sitcom cartoons.
The Maxx | 1995 | Western series | US | Superhero, Psychological, Surreal | A | Strange, compact MTV adaptation with a unique visual identity.
Todd McFarlane's Spawn | 1997 | Western series | US | Superhero, Horror, Crime | A+ | Existing Spawn entry clarified as the HBO series.
Batman: Gotham Knight | 2008 | Western anthology film | US / Japan | Superhero, Action, Anthology | A | Batman stories animated by major Japanese studios; uneven but visually worthwhile.
Halo Legends | 2010 | Western anthology film | US / Japan | Sci-Fi, Action, Anthology | A | Halo interpreted by multiple anime studios; several shorts are excellent.

# --- Adult / erotic / extreme-content lane (quality still required) ---
Golden Boy | 1995 | OVA | Japan | Comedy, Ecchi, Adult | A+ | Existing pick retained; outrageous but exceptionally animated comedy.
Interspecies Reviewers | 2020 | Series | Japan | Fantasy, Sex Comedy, Ecchi | A | Existing pick retained for its complete commitment to the premise.
High School DxD | 2012 | Series | Japan | Action, Ecchi, Fantasy | A | Existing pick retained; fanservice plus actual battle progression.
Highschool of the Dead | 2010 | Series | Japan | Zombies, Action, Ecchi | A+ | Existing pick retained; Madhouse action spectacle with shameless fanservice.
Rin: Daughters of Mnemosyne | 2008 | OVA | Japan | Horror, Erotic Thriller, Adult | A | Existing pick retained; explicit and exploitative, but committed adult horror noir.
Wicked City | 1987 | Film | Japan | Horror, Erotic, Noir | A | Existing pick retained; substantial sexual violence warning.
Belladonna of Sadness | 1973 | Film | Japan | Adult, Experimental, Drama | S | Psychedelic landmark with explicit sexual violence; not casual viewing.
Lupin the Third: The Woman Called Fujiko Mine | 2012 | Series | Japan | Crime, Adult, Erotic | S | Adult sexuality used as part of a strong visual and character reinvention.

# --- Additional quality picks / genre breadth ---
Natsume's Book of Friends | 2008 | Series | Japan | Supernatural, Drama, Episodic | S | Gentle but consistently excellent; emotional payoff rather than plot urgency.
Laid-Back Camp | 2018 | Series | Japan | Slice-of-life, Travel, Comedy | A+ | Relaxing is the point, but craftsmanship and place-based storytelling keep it engaging.
Spy x Family | 2022 | Series | Japan | Comedy, Action, Family | A+ | Family comedy plus espionage set pieces and excellent production.
Barakamon | 2014 | Series | Japan | Comedy, Slice-of-life, Art | A+ | Rural comedy with real artistic growth and a compact runtime.
Silver Spoon | 2013 | Series | Japan | School, Agriculture, Comedy | A+ | Arakawa turns agricultural school into a smart, funny coming-of-age story.
Usagi Drop | 2011 | Series | Japan | Drama, Family, Slice-of-life | A | The anime is a warm, self-contained parenting story; stop before later manga material.
Non Non Biyori | 2013 | Series | Japan | Slice-of-life, Comedy | A | Extremely relaxed, but comic timing and rural atmosphere are excellent.
Hakumei and Mikochi | 2018 | Series | Japan | Fantasy, Slice-of-life | A | Miniature-world craftsmanship gives every episode visual texture.
Aria the Animation | 2005 | Series | Japan | Sci-Fi, Slice-of-life, Iyashikei | S | Patient by design, but one of the genre's great atmosphere-and-character achievements.
Girls' Last Tour | 2017 | Series | Japan | Post-apocalypse, Slice-of-life, Philosophy | A+ | Quiet conversations against a ruined world create real existential weight.
Do It Yourself!! | 2022 | Series | Japan | Slice-of-life, Craft, Comedy | A | Expressive animation and tactile craft detail make the low-stakes premise lively.
Super Cub | 2021 | Series | Japan | Slice-of-life, Travel | A | Minimalist but purposeful story of independence through a motorbike.
Skip and Loafer | 2023 | Series | Japan | Comedy, Drama, School | A+ | Existing addition retained.
My New Boss Is Goofy | 2023 | Series | Japan | Workplace, Comedy | A | Gentle workplace recovery comedy with strong character charm.
Aggretsuko | 2018 | Series | Japan | Workplace, Comedy, Music | A | Adult work frustrations turned into death-metal catharsis.
Polar Bear Cafe | 2012 | Series | Japan | Comedy, Slice-of-life | A | Long but reliably charming absurdist cafe comedy.

# --- More fantasy / supernatural / character pieces ---
Monogatari Series | 2009 | Series | Japan | Supernatural, Dialogue, Mystery | S+ | One of anime's most distinctive long-form directorial/wordplay projects; use the franchise guide.
Katanagatari | 2010 | Series | Japan | Adventure, Dialogue, Romance | S | Twelve double-length episodes build to an unforgettable final run.
Bakemonogatari | 2009 | Series | Japan | Supernatural, Dialogue, Mystery | S | Core entry retained within the broader Monogatari guide.
Kizumonogatari | 2016 | Film trilogy | Japan | Supernatural, Action, Horror | S+ | Visually extravagant prequel trilogy and one of Shaft's technical peaks.
Nisemonogatari | 2012 | Series | Japan | Supernatural, Dialogue, Comedy | A+ | More indulgent than Bake but crucial to the franchise's character web.
Monogatari Series Second Season | 2013 | Series | Japan | Supernatural, Drama, Mystery | S+ | Many of the franchise's strongest arcs.
Owarimonogatari | 2015 | Series | Japan | Mystery, Supernatural, Drama | S | Major resolution phase for Araragi's story.
Zoku Owarimonogatari | 2018 | Film / Series | Japan | Supernatural, Drama | A+ | Strong reflective coda after the main ending.
The Ancient Magus' Bride | 2017 | Series | Japan | Fantasy, Folklore, Drama | A+ | Existing addition retained.
Noragami Aragoto | 2015 | Series | Japan | Action, Supernatural, Drama | A+ | The stronger Noragami season, with better stakes and villain work.
Blood Blockade Battlefront | 2015 | Series | Japan | Urban Fantasy, Action, Comedy | A+ | Bones chaos, great music and constant visual invention.
Blood Blockade Battlefront & Beyond | 2017 | Series | Japan | Urban Fantasy, Action, Comedy | A | More episodic but consistently stylish continuation.
Beyond the Boundary | 2013 | Series | Japan | Supernatural, Action, Romance | A | Kyoto Animation spectacle with a compact supernatural plot.
The Devil Is a Part-Timer! Season 1 | 2013 | Series | Japan | Comedy, Fantasy, Workplace | A | First season is the essential comic premise at its sharpest.
Kyousougiga | 2013 | Series | Japan | Fantasy, Surreal, Family | A+ | Existing addition retained.

# --- More crime / adult / historical ---
Master Keaton | 1998 | Series | Japan | Mystery, Adventure, Adult | A+ | Adult episodic mysteries with archaeology, geopolitics and unusually grounded protagonists.
Gallery Fake | 2005 | Series | Japan | Art, Mystery, Adult | A | Art-world capers and authentication mysteries with an adult lead.
The Fable | 2024 | Series | Japan | Crime, Comedy, Hitman | A | Production is modest, but the deadpan assassin story is extremely entertaining.
Odd Taxi | 2021 | Series | Japan | Crime, Mystery, Black Comedy | S+ | Existing pick retained.
Black Lagoon: Roberta's Blood Trail | 2010 | OVA | Japan | Crime, Action, War | A+ | Black Lagoon at its most vicious and politically ugly.
Jormungand | 2012 | Series | Japan | Crime, Arms Dealers, Action | A+ | International arms-dealer thriller with an adult ensemble and brisk missions.
Gangsta. | 2015 | Series | Japan | Crime, Action, Adult | A | Production collapse prevents greatness, but the city/mercenary setup is compelling enough to recommend with caveat.
Michiko & Hatchin | 2008 | Series | Japan | Crime, Road, Adventure | A+ | Stylish Brazil-inspired road adventure with strong adult character energy.
Baccano! Specials | 2008 | Special | Japan | Crime, Supernatural, Comedy | A | Worth watching after the main 13 episodes to complete several threads.
Durarara!! | 2010 | Series | Japan | Urban Fantasy, Crime, Ensemble | A+ | Large Ikebukuro ensemble where storylines collide with satisfying regularity.
Durarara!!x2 | 2015 | Series | Japan | Urban Fantasy, Crime, Ensemble | A | More sprawling continuation; best if you already love the cast.

# --- Magical girl / shoujo / josei breadth ---
Puella Magi Madoka Magica the Movie: Rebellion | 2013 | Film | Japan | Magical Girl, Psychological, Fantasy | S+ | Essential, visually extravagant sequel to Madoka.
Revolutionary Girl Utena: Adolescence of Utena | 1999 | Film | Japan | Fantasy, Romance, Surreal | S | Not a recap; a radical alternate film interpretation.
Princess Tutu | 2002 | Series | Japan | Magical Girl, Fantasy, Drama | S | Existing addition retained.
Cardcaptor Sakura | 1998 | Series | Japan | Magical Girl, Fantasy | S | Existing addition retained.
HeartCatch PreCure! | 2010 | Series | Japan | Magical Girl, Action | A+ | One of Precure's strongest seasons: expressive action and genuine character growth.
Go! Princess PreCure | 2015 | Series | Japan | Magical Girl, Action, Fantasy | A | Excellent transformation/action craft and a strong thematic spine.
Ojamajo Doremi | 1999 | Series | Japan | Magical Girl, Comedy, Drama | A+ | Long but unusually perceptive about childhood and consequences.
Rose of Versailles | 1979 | Series | Japan | Historical, Drama, Romance | S+ | Existing classic addition retained.
Dear Brother | 1991 | Series | Japan | Drama, Psychological, School | A+ | Dezaki-directed shoujo melodrama pushed to operatic extremes.
Oniisama e... | 1991 | Series | Japan | Drama, Psychological, School | A+ | Alias of Dear Brother handled during build.
Nodame Cantabile | 2007 | Series | Japan | Music, Romance | S | Existing addition retained.
Chihayafuru | 2011 | Series | Japan | Sports, Drama, Romance | S+ | Existing addition retained.

# --- Short/OVA curiosities that are genuinely worth the time ---
Pale Cocoon | 2005 | OVA | Japan | Sci-Fi, Mystery | A | Twenty-three-minute environmental sci-fi mystery with a strong visual idea.
Time of Eve | 2008 | ONA | Japan | Sci-Fi, AI, Drama | S | Existing addition retained.
She and Her Cat: Everything Flows | 2016 | Series | Japan | Drama, Short | A | Short emotional mini-series expanding Shinkai's original concept.
She and Her Cat | 1999 | Short Film | Japan | Drama, Short | A | Five-minute early Shinkai miniature.
Voices of a Distant Star | 2002 | Short Film | Japan | Sci-Fi, Romance | A | Existing addition retained.
Cat Soup | 2001 | OVA | Japan | Surreal, Dark Comedy | A+ | Thirty minutes of cute design and deeply strange existential imagery.
Puparia | 2020 | Short Film | Japan | Experimental, Animation | A | Three minutes of breathtaking independent animation craft.

# --- Donghua / Chinese animation ---
Fog Hill of Five Elements | 2020 | Donghua series | China | Action, Fantasy, Martial Arts | S | Hand-drawn action showcase with extraordinary brushlike animation.
Link Click | 2021 | Donghua series | China | Mystery, Time Travel, Drama | S | Existing pick retained.
Heaven Official's Blessing | 2020 | Donghua series | China | Fantasy, Romance, Adventure | A+ | Lush xianxia/danmei adaptation with strong atmosphere.
Mo Dao Zu Shi | 2018 | Donghua series | China | Fantasy, Mystery, Action | A+ | Dense cultivation mystery with excellent visual design.
Scissor Seven | 2018 | Donghua series | China | Action, Comedy, Drama | A+ | Silly assassin comedy that gradually reveals a surprisingly strong action/drama spine.
The King's Avatar | 2017 | Donghua series | China | Esports, Gaming, Drama | A | Clean competence fantasy centered on professional esports.
A Will Eternal | 2020 | Donghua series | China | Cultivation, Comedy, Action | A | Long-form cultivation comedy with escalating spectacle.
Blades of the Guardians | 2023 | Donghua series | China | Historical, Action, Martial Arts | A+ | Gritty wuxia road action with strong choreography.
The Ravages of Time | 2023 | Donghua series | China | Historical, War, Strategy | A | Three Kingdoms strategy in a visually ambitious CG adaptation.
Lord of Mysteries | 2025 | Donghua series | China | Dark Fantasy, Mystery, Steampunk | S | Existing elite donghua pick retained.
To Be Hero X | 2025 | Donghua series | China / Japan | Superhero, Action, Experimental | S | Existing pick retained; unusual mixed-media superhero production.

# --- Additional western/anime crossover projects ---
Cyberpunk: Edgerunners | 2022 | Series | Japan / Poland | Cyberpunk, Action, Drama | S+ | Existing elite pick retained.
Terminator Zero | 2024 | Series | Japan / US | Sci-Fi, Action, Time Travel | A+ | Existing pick retained.
Scott Pilgrim Takes Off | 2023 | Western series | US / Japan | Comedy, Action, Romance | A+ | Existing pick retained.
Super Crooks | 2021 | Series | Japan / US | Crime, Superhero, Action | A | Bones animates a stylish supervillain heist story.
Cannon Busters | 2019 | Western series | US / Japan | Adventure, Sci-Fi, Action | A | Uneven but charming anime-Western road adventure.
Dante's Inferno: An Animated Epic | 2010 | Western anthology film | US / Japan | Dark Fantasy, Horror, Anthology | B+ | Uneven anthology, but the studio-to-studio visual changes make it an interesting adult-animation artifact.

# --- Current/near-current selections from 2025-2026 worth tracking ---
My Hero Academia FINAL SEASON | 2025 | Series | Japan | Superhero, Action, Drama | S | 2026 Crunchyroll Anime of the Year winner and the franchise's conclusion.
The Apothecary Diaries Season 2 | 2025 | Series | Japan | Mystery, Historical, Drama | S+ | Award-winning direction and an even stronger continuation of the palace mystery format.
DAN DA DAN Season 2 | 2025 | Series | Japan | Action, Supernatural, Comedy | S | Maintains the franchise's high-energy visual identity.
Takopi's Original Sin | 2025 | Series | Japan | Psychological, Drama, Sci-Fi | S | Existing pick retained.
Gachiakuta | 2025 | Series | Japan | Action, Dark Fantasy | S | Existing pick retained and 2026 Best New Series winner.
Lazarus | 2025 | Series | Japan | Sci-Fi, Action, Thriller | A+ | Existing pick retained and 2026 Best Original Anime winner.
Clevatess | 2025 | Series | Japan | Dark Fantasy, Adventure | A+ | Existing pick retained and a 2026 Best New Series nominee.
SAKAMOTO DAYS | 2025 | Series | Japan | Action, Comedy, Crime | A | Existing pick retained; animation is not always elite, but the assassin-comedy momentum works.
The Summer Hikaru Died | 2025 | Series | Japan | Horror, Mystery, Drama | S | Existing pick retained.
100 Meters | 2025 | Film | Japan | Sports, Drama | S | Current awards-era film pick retained.

'''


# Additional studio/format pass. The rule is still quality first: these are here because they
# add genuinely worthwhile work or fill a major creative lineage, not to make collection counts look large.
STUDIO_EXPANSION = r'''Food Wars! Shokugeki no Soma | 2015 | Series | Japan | Comedy, Cooking, Competition | A+ | Ridiculous culinary battles with tournament-anime momentum; strongest in the earlier seasons.
A Certain Scientific Railgun | 2009 | Series | Japan | Sci-Fi, Action, Superpowers | A+ | The Railgun branch grows into the sharpest and most consistently exciting corner of the Index franchise.
The Pet Girl of Sakurasou | 2012 | Series | Japan | Romance, Drama, Comedy | A+ | Creative ambition, failure and romance with much more emotional bite than its dorm-comedy setup suggests.
Honey and Clover | 2005 | Series | Japan | Drama, Romance, Art School | S | Adult-feeling uncertainty, unrequited love and creative ambition from an unusually observant ensemble drama.
Excel Saga | 1999 | Series | Japan | Comedy, Parody, Experimental | A | Hyperactive genre parody that deliberately destroys a different convention whenever it gets the chance.
Hi Score Girl | 2018 | Series | Japan | Romance, Comedy, Gaming | A+ | Arcade history and awkward young romance become a surprisingly addictive long-form rivalry.
Flying Witch | 2016 | Series | Japan | Slice-of-life, Fantasy, Comedy | A | Gentle rather than inert: small supernatural discoveries, excellent timing and a genuinely relaxing sense of place.
Maid-Sama! | 2010 | Series | Japan | Romance, Comedy, School | A | A durable shoujo rom-com driven by two leads who actually generate comic friction.
Is It Wrong to Try to Pick Up Girls in a Dungeon? | 2015 | Series | Japan | Fantasy, Action, Adventure | A | Better dungeon progression and later dramatic arcs than the title suggests; season four is a particular high point.
The Duke of Death and His Maid | 2021 | Series | Japan | Romance, Fantasy, Comedy | A | A cursed romance that steadily advances instead of resetting the relationship every episode.
Rurouni Kenshin (1996) | 1996 | Series | Japan | Samurai, Action, Historical | S | The Kyoto arc remains one of television anime's defining sword-action stories despite the adaptation's later filler.
Sasaki and Miyano | 2022 | Series | Japan | Romance, BL, Comedy | A+ | Warm, funny BL romance with clear progression and unusually likable character dynamics.
Read or Die OVA | 2001 | OVA | Japan | Action, Espionage, Superpowers | A+ | Three episodes of gloriously overqualified paper-powered spy action with feature-quality set pieces.
You're Under Arrest | 1994 | OVA | Japan | Police, Comedy, Action | A+ | Charming buddy-cop animation with mechanical detail, great vehicle action and effortless character chemistry.
GetBackers | 2002 | Series | Japan | Action, Supernatural, Comedy | A | A very 2000s supernatural retrieval-team adventure that stays fun through powers, rivalries and escalating missions.
The Rising of the Shield Hero | 2019 | Series | Japan | Isekai, Fantasy, Adventure | A | Season one has a strong persecution-to-progression hook; later seasons are substantially more uneven.
Princess Jellyfish | 2010 | Series | Japan | Comedy, Romance, Josei | S | A funny, humane adult ensemble about identity, confidence and an apartment full of obsessive misfits.
My Teen Romantic Comedy SNAFU | 2013 | Series | Japan | Romance, Drama, Comedy | S | Acerbic social observation evolves into one of anime's more psychologically tangled relationship dramas.
Mawaru Penguindrum | 2011 | Series | Japan | Psychological, Drama, Surreal | S+ | Kunihiko Ikuhara turns family trauma, fate and terrorism into a dense but emotionally forceful visual puzzle.
My Little Monster | 2012 | Series | Japan | Romance, Comedy, School | A | Volatile leads and fast relationship movement keep this school romance from settling into routine.
Hotarubi no Mori e | 2011 | Film | Japan | Romance, Supernatural, Drama | S | A short supernatural romance that earns a disproportionate emotional impact in under an hour.
In/Spectre | 2020 | Series | Japan | Mystery, Supernatural, Romance | A | Dialogue-heavy supernatural deduction becomes entertaining through its argumentative leads and unusual cases.
Symphogear | 2012 | Series | Japan | Action, Music, Sci-Fi | A+ | Songs are literally combat mechanics in an increasingly maximalist franchise that keeps finding a bigger gear.
Macross Delta | 2016 | Series | Japan | Mecha, Music, Sci-Fi | A | Idol tactical units, aerial combat and franchise-scale melodrama in a colorful standalone-era Macross entry.
Aquarion EVOL | 2012 | Series | Japan | Mecha, Romance, Sci-Fi | A | Shamelessly operatic mecha romance with spectacular Satelight design work and a commitment to its own absurdity.
White Album 2 | 2013 | Series | Japan | Romance, Drama, Music | S | A compact love triangle in which every bad decision feels understandable, making the emotional damage land harder.
AKB0048 | 2012 | Series | Japan | Music, Sci-Fi, Action | A | An idol show built as space-opera resistance fiction; much stranger and more energetic than the premise sounds.
Fairy Tail | 2009 | Series | Japan | Fantasy, Action, Adventure | A | Huge, uneven and extremely sincere, but its best guild battles and emotional payoffs explain the franchise's durability.
Somali and the Forest Spirit | 2020 | Series | Japan | Fantasy, Adventure, Drama | A+ | Gorgeous travel fantasy whose surrogate-parent bond provides a real deadline and emotional stakes.
BLAME! | 2017 | Film | Japan | Sci-Fi, Action, Cyberpunk | A+ | Monumental architecture and hostile machine ecology translated into a lean CG survival film.
Levius | 2019 | Series | Japan | Boxing, Steampunk, Sci-Fi | A | Mechanical boxing with strong CG fight direction and a compact tournament-driven arc.
Pacific Rim: The Black | 2021 | Western series | US / Japan | Mecha, Kaiju, Survival | A | A grim animated side-route through Pacific Rim with kaiju action, survival pressure and serialized momentum.
Kaina of the Great Snow Sea | 2023 | Series | Japan | Sci-Fi, Adventure, Fantasy | A | Tsutomu Nihei-style worldbuilding in a more accessible adventure structure with striking giant-scale environments.
Summertime Rendering | 2022 | Series | Japan | Mystery, Time Loop, Thriller | S+ | A tightly escalating island time-loop thriller that keeps changing the rules before repetition can become stale.
Komi Can't Communicate | 2021 | Series | Japan | Comedy, Romance, School | A+ | Lavish visual comedy and a huge eccentric cast keep the social-anxiety premise buoyant and inventive.
Inazuma Eleven | 2008 | Series | Japan | Sports, Football, Superpowers | A | Football treated as unapologetic battle fantasy, ideal when conventional sports realism sounds too restrained.
Utawarerumono | 2006 | Series | Japan | Fantasy, War, Drama | A+ | Starts as village fantasy and expands into war, politics and identity with a satisfying strategic backbone.
New Game! | 2016 | Series | Japan | Workplace, Comedy, Games | A | Bright workplace comedy elevated by strong character animation and genuine interest in game production.
YuruYuri | 2011 | Series | Japan | Comedy, Slice-of-life, School | A+ | Exceptionally efficient ensemble comedy whose running gags keep mutating instead of simply repeating.
Gabriel DropOut | 2017 | Series | Japan | Comedy, Supernatural, School | A | Angels and demons become terrible roommates in a consistently sharp character-comedy setup.
Plastic Memories | 2015 | Series | Japan | Romance, Sci-Fi, Drama | A+ | The expiration-date premise makes its romance knowingly tragic without requiring a surprise twist to work.
Chivalry of a Failed Knight | 2015 | Series | Japan | Action, Fantasy, Romance | A | A tournament-school setup that benefits enormously from letting its central romance actually progress.
The Misfit of Demon King Academy | 2020 | Series | Japan | Fantasy, Action, Comedy | A | Ridiculous overpowered fantasy that understands the entertainment value of taking invincibility past parody.
My Next Life as a Villainess | 2020 | Series | Japan | Isekai, Romance, Comedy | A+ | The villainess-isekai boom's most charming early hit, driven by a lead who accidentally collects the entire cast.
Restaurant to Another World | 2017 | Series | Japan | Fantasy, Food, Anthology | A | Comfort-food anthology with enough fantasy-world variety to make each new customer feel like a small story discovery.
Tanaka-kun Is Always Listless | 2016 | Series | Japan | Comedy, Slice-of-life | A+ | Immaculate comic timing turns weaponized laziness into a surprisingly precise character comedy.
Dusk Maiden of Amnesia | 2012 | Series | Japan | Supernatural, Romance, Mystery | A | Haunted-school romance that balances playful chemistry with an increasingly tragic ghost story.
Call of the Night | 2022 | Series | Japan | Romance, Vampires, Nightlife | S | Neon night direction, a superb soundtrack and languid flirtation give the series an immediately recognizable identity.
Cells at Work! Code Black | 2021 | Series | Japan | Biology, Action, Dark Comedy | A | The body-as-workplace conceit becomes a much harsher survival story inside an unhealthy adult body.
Terraformars | 2014 | Series | Japan | Sci-Fi, Action, Horror | A | Pulpy Mars survival with grotesque evolutionary powers and a brutally direct first-season hook.
Re:Creators | 2017 | Series | Japan | Action, Meta, Fantasy | S | Fictional characters invade the real world and force creators to confront responsibility for the suffering they write.
Overtake! | 2023 | Series | Japan | Motorsport, Drama, Photography | A+ | Grounded Formula 4 racing shares space with adult trauma and photography without sacrificing race-day tension.
IDOLiSH7 | 2018 | Series | Japan | Music, Drama, Idol | A+ | One of the stronger idol dramas because careers, management and group conflict have persistent consequences.
Lord El-Melloi II's Case Files | 2019 | Series | Japan | Mystery, Magic, Fate | A+ | Fate's magic system becomes an occult detective framework with a welcome adult lead and atmosphere.
Aldnoah.Zero | 2014 | Series | Japan | Mecha, War, Sci-Fi | A | Excellent tactical mecha battles and music carry a series whose second half is much more divisive than its first.
Beautiful Bones: Sakurako's Investigation | 2015 | Series | Japan | Mystery, Forensics, Drama | A | Forensic mysteries anchored by an eccentric osteologist and a restrained, autumnal atmosphere.
Wandering Witch: The Journey of Elaina | 2020 | Series | Japan | Fantasy, Travel, Anthology | A+ | A beautiful travel anthology willing to swing from whimsical to genuinely nasty without warning.
TSUKIMICHI -Moonlit Fantasy- | 2021 | Series | Japan | Isekai, Fantasy, Comedy | A | Fast-moving power fantasy with a useful comic streak and a world that grows beyond the initial rejection gimmick.
Onimai: I'm Now Your Sister! | 2023 | Series | Japan | Comedy, Slice-of-life, Gender-bender | A+ | Controversial premise, but astonishingly expressive everyday animation and inventive visual comedy.
Assassination Classroom | 2015 | Series | Japan | Action, Comedy, School | S | A bizarre killer-teacher premise develops into a complete class ensemble with an unusually satisfying ending.
Scum's Wish | 2017 | Series | Japan | Romance, Drama, Psychological | A+ | A deliberately uncomfortable romance about desire, substitution and self-deception, presented with visual confidence.
Toilet-Bound Hanako-kun | 2020 | Series | Japan | Supernatural, Mystery, Romance | A+ | Graphic color design and playful ghost mythology give a familiar school-supernatural setup a strong personality.
Monster Musume | 2015 | Series | Japan | Ecchi, Comedy, Monster Girls | A | Shameless monster-girl harem comedy with strong timing and far more animation personality than required.
A Whisker Away | 2020 | Film | Japan | Romance, Fantasy, Coming-of-age | A+ | Adolescent obsession becomes body-swapping cat fantasy with energetic visuals and a real emotional endpoint.
Burn the Witch | 2020 | OVA | Japan | Fantasy, Action, Dragons | A+ | Compact Tite Kubo worldbuilding with excellent dragon action and almost no onboarding drag.
Pokémon: Twilight Wings | 2020 | ONA | Japan | Fantasy, Drama, Anthology | A+ | Short-form Pokémon storytelling with gorgeous Colorido animation and unusually human-scale vignettes.
Drifting Home | 2022 | Film | Japan | Fantasy, Adventure, Drama | A | Children adrift on a floating apartment block make for a visually imaginative, emotionally direct survival fantasy.
Mieruko-chan | 2021 | Series | Japan | Horror, Comedy, Supernatural | A+ | A great comic-horror mechanism: the heroine sees nightmare creatures and survives by pretending she absolutely does not.
Rokka: Braves of the Six Flowers | 2015 | Series | Japan | Fantasy, Mystery, Action | A+ | A chosen-heroes quest abruptly becomes a locked-room impostor mystery, which is much more interesting than the setup.
Citrus | 2018 | Series | Japan | Romance, Drama, Yuri | A | Messy melodrama rather than gentle romance; compelling if you want emotional friction and escalating relationship stakes.
Masters of the Universe: Revelation | 2021 | Western series | US | Fantasy, Action, Adventure | A | Powerhouse turns toy-box fantasy into muscular serialized sword-and-sorcery with excellent combat animation.
Masters of the Universe: Revolution | 2024 | Western series | US | Fantasy, Action, Adventure | A | A tighter continuation that doubles down on Powerhouse's spectacle and pulp sincerity.
Kipo and the Age of Wonderbeasts | 2020 | Western series | US / South Korea | Adventure, Sci-Fi, Music | S | Colorful post-apocalyptic adventure with great music, brisk serialized plotting and a genuinely imaginative ecosystem.
X-Men '97 | 2024 | Western series | US / South Korea | Superhero, Action, Drama | S+ | Dense serialized superhero melodrama with unusually forceful action staging and consequences that actually stick.
Lookism | 2022 | Series | South Korea | Drama, School, Social Thriller | A+ | Body-swapping social drama that turns beauty hierarchy, bullying and street fights into a propulsive webtoon adaptation.
Murder Drones | 2021 | Western web series | US / Australia | Sci-Fi, Horror, Comedy | A+ | Indie CG web animation with anime-inflected action, fast lore escalation and unusually polished character work.
Mars Express | 2023 | Western film | France | Sci-Fi, Cyberpunk, Mystery | S | Adult cyberpunk detective fiction with clean visual design, hard ideas and a satisfying feature-length mystery.
Lastman | 2016 | Western series | France | Action, Fantasy, Crime | S | French adult animation with manga DNA, brutal fights and a serialized occult-crime story that moves fast.
Wakfu | 2008 | Western series | France | Fantasy, Adventure, Action | S | French anime-influenced fantasy that grows from colorful questing into increasingly ambitious long-form mythology.
Ne Zha | 2019 | Animated film | China | Fantasy, Action, Mythology | S | Huge Chinese mythological blockbuster with elastic comedy, spectacular action and a strong rebellious core.
Ne Zha 2 | 2025 | Animated film | China | Fantasy, Action, Mythology | S+ | An enormous sequel that pushes Chinese CG spectacle, scale and kinetic action far beyond the first film.
Deep Sea | 2023 | Animated film | China | Fantasy, Drama, Adventure | S | Painterly CG imagery carries a psychologically dark fantasy whose visual imagination is the main event.
White Snake | 2019 | Animated film | China | Fantasy, Romance, Action | A+ | Mythic romance with fluid action and a polished CG aesthetic that helped define the modern Chinese feature boom.
Green Snake | 2021 | Animated film | China | Fantasy, Action, Adventure | A | A stranger, more action-heavy White Snake follow-up built around a surreal purgatorial city.
I Am What I Am | 2021 | Animated film | China | Sports, Drama, Comedy | S | Lion-dance competition becomes a terrific underdog sports film with grounded class detail and superb movement.
The Legend of Hei | 2019 | Animated film | China | Fantasy, Action, Adventure | S | Warm character comedy and astonishingly clean action choreography in a modern-spirit fantasy world.
A Record of a Mortal's Journey to Immortality | 2020 | Donghua series | China | Cultivation, Fantasy, Adventure | A+ | Patient but rewarding cultivation progression with unusually convincing CG environments and long-form worldbuilding.
Free! | 2013 | Series | Japan | Swimming, Sports, Drama | A+ | Kyoto Animation turns competitive swimming into polished character drama with excellent movement and rivalry arcs.
Armored Trooper Votoms | 1983 | Series | Japan | Mecha, War, Sci-Fi | S | Hard-edged military mecha where machines feel disposable and survival matters more than heroic super-robot spectacle.
Giant Robo: The Day the Earth Stood Still | 1992 | OVA | Japan | Super Robot, Action, Pulp | S+ | Seven episodes of operatic retro-futurist spectacle, enormous personalities and absurdly beautiful hand-drawn action.
Full Metal Panic! | 2002 | Series | Japan | Mecha, Action, Comedy | S | Military thriller and school comedy should not fit together this well; The Second Raid is the dramatic peak.
Space Runaway Ideon | 1980 | Series | Japan | Mecha, Sci-Fi, Tragedy | S | Tomino's apocalyptic space opera becomes increasingly uncompromising and culminates in one of mecha anime's defining endings.
The King of Braves GaoGaiGar | 1997 | Series | Japan | Super Robot, Action, Sci-Fi | A+ | The super-robot formula performed with so much conviction and escalation that the Final OVA becomes genuinely epic.
Gun x Sword | 2005 | Series | Japan | Mecha, Western, Revenge | A+ | A revenge road story with giant robots, eccentric villains and an excellent second-half acceleration.
Patlabor: The Early Days | 1988 | OVA | Japan | Mecha, Police, Comedy | S | Workplace police comedy, grounded robotics and Oshii weirdness establish the most likable corner of the Patlabor universe.
A Sign of Affection | 2024 | Series | Japan | Romance, Drama, College | A+ | College romance with expressive visual communication and adults who are capable of actually talking to one another.
The Dangers in My Heart | 2023 | Series | Japan | Romance, Comedy, School | S | Starts deliberately awkward and then becomes one of recent anime's most carefully observed relationship progressions.
Kimi ni Todoke | 2009 | Series | Japan | Romance, Drama, School | S | Patient shoujo romance justified by exceptional character warmth, social tension and long-earned emotional releases.
Lovely Complex | 2007 | Series | Japan | Romance, Comedy, School | A+ | Height-complex banter gives way to a lively romance with loud personalities and strong comic timing.
My Love Story!! | 2015 | Series | Japan | Romance, Comedy | A+ | A rom-com that gets past the confession early and finds comedy in maintaining an unusually wholesome relationship.
Orange | 2016 | Series | Japan | Drama, Romance, Time Travel | A+ | Future letters turn high-school regret into a race against a preventable tragedy.
Wotakoi: Love Is Hard for Otaku | 2018 | Series | Japan | Romance, Comedy, Workplace | A+ | Adult nerds date without pretending romance requires high-school misunderstandings, and the ensemble chemistry carries it.
Josee, the Tiger and the Fish | 2020 | Film | Japan | Romance, Drama | S | A feature-length romance with ambition, disability, conflict and a satisfying visual/emotional arc.
I Want to Eat Your Pancreas | 2018 | Film | Japan | Drama, Romance, Tragedy | S | A deliberately direct tearjerker, but one built around lively chemistry rather than passive sentimentality.
Wasteful Days of High School Girls | 2019 | Series | Japan | Comedy, School | A | A stupid-in-the-best-way ensemble comedy whose character nicknames are basically self-sustaining joke engines.
Detroit Metal City | 2008 | OVA | Japan | Comedy, Music, Adult | A+ | Extremely profane identity comedy about a timid pop songwriter accidentally becoming a death-metal monster.
Cromartie High School | 2003 | Series | Japan | Comedy, Delinquents, Absurdist | A+ | Deadpan absurdism so committed that robots, gorillas and Freddie Mercury barely register as unusual classmates.
Ayakashi: Samurai Horror Tales | 2006 | Anthology series | Japan | Horror, Historical, Supernatural | A+ | Uneven anthology overall, but the Bakeneko arc is the direct visual and thematic launchpad for Mononoke.
Pet Shop of Horrors | 1999 | OVA | Japan | Horror, Supernatural, Anthology | A | Four compact morality tales where exotic pets expose exactly what their owners are trying not to admit.
The Imaginary | 2023 | Film | Japan | Fantasy, Adventure, Drama | S | Studio Ponoc's most confident feature: imaginative worlds, real emotional stakes and exceptionally polished hand-drawn fantasy.
Mary and The Witch's Flower | 2017 | Film | Japan | Fantasy, Adventure | A+ | A beautifully animated Ghibli-descended fantasy adventure that moves briskly even when the story is more familiar than its craft.
Modest Heroes | 2018 | Film anthology | Japan | Fantasy, Drama, Adventure | A+ | Three compact Studio Ponoc shorts with radically different scales, from tiny survival to human drama and action.
'''
EXTRA += "\n" + STUDIO_EXPANSION

FRANCHISE_EXTRA_TITLES = r'''Black Butler | 2008 | Series | Japan | Gothic, Mystery, Supernatural | A+ | The franchise is excellent when following the manga-canon route; use the franchise map because the early anime diverges heavily.
Violet Evergarden: Eternity and the Auto Memory Doll | 2019 | Film | Japan | Drama, Emotional, Fantasy | S | A beautifully made side story that expands Violet's world before the final film.
Violet Evergarden: The Movie | 2020 | Film | Japan | Drama, Emotional, Romance | S+ | The feature-length conclusion gives the series its largest emotional and visual payoff.
Made in Abyss: Dawn of the Deep Soul | 2020 | Film | Japan | Dark Fantasy, Adventure, Horror | S | Mandatory bridge between the first and second television seasons, with some of the franchise's strongest material.
Made in Abyss: The Golden City of the Scorching Sun | 2022 | Series | Japan | Dark Fantasy, Adventure, Horror | S | A horrifying, imaginative second season that pays off the film and expands the Abyss mythology dramatically.
Code Geass: Lelouch of the Re;surrection | 2019 | Film | Japan | Mecha, Political Thriller, Sci-Fi | A+ | A sequel to the recap-movie continuity rather than the original TV ending; best approached with the franchise map.
The Garden of Sinners: Future Gospel | 2013 | Film | Japan | Supernatural, Mystery, Drama | A+ | A rewarding later epilogue/side story after the core seven-film Kara no Kyoukai sequence.
'''
EXTRA += "\n" + FRANCHISE_EXTRA_TITLES

# Explicit alias equivalence for deduplication. Keys are normalized title variants.
ALIASES = {
    'kimi no na wa':'Your Name',
    'kimi no na wa.':'Your Name',
    'shingeki no kyojin':'Attack on Titan',
    'hagane no renkinjutsushi brotherhood':'Fullmetal Alchemist: Brotherhood',
    'haikyuu':'Haikyu!!',
    'haikyuu!!':'Haikyu!!',
    'oniisama e':'Dear Brother',
    'oniisama e...':'Dear Brother',
    'kubikiri cycle':'Kubikiri Cycle',
    'the kubikiri cycle':'Kubikiri Cycle',
    'to be hero x':'TO BE HERO X',
    'sakamoto days':'Sakamoto Days',
    'monogatari series':'Monogatari Series',
    'todd mcfarlanes spawn':'Spawn',
    'todd mcfarlane s spawn':'Spawn',
    'todd mcfarlanes spawn':'Spawn',
    'heike story':'Heike Monogatari',
    'shinsekai yori':'From the New World',
    'summertime rendering':'Summer Time Rendering',
    'elusive samurai':'Elusive Samurai',
}

def norm(s):
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode('ascii').lower()
    s=s.replace('&',' and ')
    s=re.sub(r'\b(the|a|an)\b',' ',s)
    s=re.sub(r'[^a-z0-9]+',' ',s)
    return re.sub(r'\s+',' ',s).strip()

def slug_id(title, year=None, typ=''):
    base=norm(title).replace(' ','-')[:70] or 'title'
    # master titles stay stable even if a stored year is corrected later
    digest=hashlib.sha1(norm(title).encode()).hexdigest()[:8]
    return f'm:{base}:{digest}'

old_by={norm(x['title']): dict(x) for x in OLD['watch']}
# Reinstate former taste-only exclusions with curated minimal metadata.
reinstate_meta={
'Spy x Family':(2022,'Series','Japan','Comedy, Action, Family','A+'),
'Fruits Basket (2019)':(2019,'Series','Japan','Drama, Romance, Supernatural','S'),
'Clannad / After Story':(2007,'Series','Japan','Drama, Romance, Supernatural','S'),
'Horimiya':(2021,'Series','Japan','Romance, Comedy, School','A+'),
'My Dress-Up Darling':(2022,'Series','Japan','Romance, Comedy, Cosplay','A+'),
'Toradora!':(2008,'Series','Japan','Romance, Comedy, Drama','A+'),
'Kaguya-sama: Love Is War':(2019,'Series','Japan','Romance, Comedy','S+'),
'Violet Evergarden':(2018,'Series','Japan','Drama, Emotional, Fantasy','S+'),
'Mushishi':(2005,'Series','Japan','Supernatural, Mystery, Atmospheric','S+'),
"Natsume's Book of Friends":(2008,'Series','Japan','Supernatural, Drama, Episodic','S'),
'Laid-Back Camp':(2018,'Series','Japan','Slice-of-life, Travel, Comedy','A+'),
'March Comes in Like a Lion':(2016,'Series','Japan','Drama, Coming-of-age','S+'),
'Your Lie in April':(2014,'Series','Japan','Music, Romance, Drama','A+'),
'A Silent Voice':(2016,'Film','Japan','Drama, Coming-of-age','S+'),
'Your Name':(2016,'Film','Japan','Romance, Drama, Supernatural','S+'),
'Weathering With You':(2019,'Film','Japan','Romance, Fantasy, Drama','A+'),
'The Garden of Words':(2013,'Film','Japan','Romance, Drama','A'),
'Anohana':(2011,'Series','Japan','Drama, Grief, Friendship','A+'),
}
for t,(y,ty,o,g,b) in reinstate_meta.items():
    old_by.setdefault(norm(t),{'title':t,'year':y,'type':ty,'origin':o,'genres':g,'why':'Re-evaluated under the genre-neutral master-list criteria.','caveat':'','watch_note':'','api':'anilist','lookupTitle':t,'provisional':False,'entertainment':8,'production':9,'story':9,'darkness':2,'explicitness':1,'fit_score':90,'tier':b,'rank':9999})

band_score={'S+':100,'S':94,'A+':88,'A':82,'B+':76,'B':70}

entries={}
for k,x in old_by.items():
    x=dict(x)
    x['quality_band']=x.get('tier','A')
    x['curation_score']=band_score.get(x['quality_band'],80) - min((x.get('rank',200)-1)/1000,1)
    x['editorial_note']=x.get('why','')
    entries[k]=x

for raw in EXTRA.splitlines():
    raw=raw.strip()
    if not raw or raw.startswith('#'): continue
    parts=[p.strip() for p in raw.split('|')]
    if len(parts)<6: continue
    title, year, typ, origin, genres, band = parts[:6]
    note=parts[6] if len(parts)>6 else ''
    if title=='Orbital Era?': continue
    key=norm(title)
    key=norm(ALIASES.get(key,title))
    canonical=ALIASES.get(norm(title), title)
    existing=entries.get(key)
    if existing:
        # Promote metadata/quality if the new curation says more.
        existing['quality_band']= band if band_score.get(band,0)>band_score.get(existing.get('quality_band','B'),0) else existing.get('quality_band',band)
        existing['curation_score']=max(existing.get('curation_score',0),band_score.get(band,80))
        if note and (not existing.get('editorial_note') or existing.get('editorial_note','').startswith('Re-evaluated')): existing['editorial_note']=note
        if not existing.get('genres') or existing.get('genres')=='Various': existing['genres']=genres
        if not existing.get('year'): existing['year']=int(year or 0)
        continue
    api='tvmaze' if typ.lower().startswith('western') and 'film' not in typ.lower() and 'anthology' not in typ.lower() else 'anilist'
    if typ.lower().startswith('western') and 'film' in typ.lower(): api='wiki'
    entries[key]={
        'title':canonical,'year':int(year or 0),'type':typ,'origin':origin,'genres':genres,
        'pace':'Varies','commitment':'Film' if 'film' in typ.lower() else ('Very short' if typ.lower() in {'ova','short film','music video'} else 'Varies'),
        'entertainment':9 if band in {'S+','S'} else 8,
        'production':10 if band=='S+' else (9 if band in {'S','A+'} else 8),
        'story':10 if band=='S+' else (9 if band in {'S','A+'} else 8),
        'darkness':2,'explicitness':1,'why':note or 'Curated for the genre-neutral master list.','editorial_note':note or 'Curated for the genre-neutral master list.',
        'caveat':'','watch_note':'','api':api,'lookupTitle':canonical,'provisional':False,'fit_score':90 if band in {'S+','S'} else 84,
        'tier':band,'quality_band':band,'curation_score':band_score.get(band,80),'sourceUrl':('https://anilist.co/search/anime?search='+re.sub(r'\s+','+',canonical)) if api=='anilist' else ('https://www.tvmaze.com/search?q='+re.sub(r'\s+','+',canonical) if api=='tvmaze' else '')
    }

# Genre-neutral re-ranking: exact top priority first, then quality band / original curation.
TOP_ORDER = [
'Attack on Titan','Fullmetal Alchemist: Brotherhood','Steins;Gate','Hunter x Hunter (2011)','Death Note','Vinland Saga','Mob Psycho 100','Arcane','Violet Evergarden','Cowboy Bebop',
'Frieren: Beyond Journey\'s End','Monster','Spirited Away','Your Name','Cyberpunk: Edgerunners','Neon Genesis Evangelion','Code Geass','Princess Mononoke','Legend of the Galactic Heroes','PLUTO',
'Made in Abyss','March Comes in Like a Lion','Kaguya-sama: Love Is War','A Silent Voice','Berserk (1997)','Samurai Champloo','Ping Pong the Animation','The Apothecary Diaries','Clannad / After Story','Haikyu!!',
'Perfect Blue','Mushishi','Odd Taxi','Chainsaw Man','DAN DA DAN','Jujutsu Kaisen','One Punch Man','Ghost in the Shell: Stand Alone Complex','Fate/Zero','Blue Eye Samurai',
'Spider-Man: Across the Spider-Verse','Spider-Man: Into the Spider-Verse','The Tatami Galaxy','Bocchi the Rock!','Mononoke','Oshi no Ko','Re:ZERO -Starting Life in Another World-','Tengen Toppa Gurren Lagann','Fruits Basket (2019)','Showa Genroku Rakugo Shinju',
'Chihayafuru','The Tale of the Princess Kaguya','Grave of the Fireflies','Wolf Children','The Girl Who Leapt Through Time','The Disappearance of Haruhi Suzumiya','Sound! Euphonium','A Place Further Than the Universe','Planetes','Mobile Suit Gundam 0080: War in the Pocket',
'Gunbuster','Macross Plus','Revolutionary Girl Utena','Nana','Kino\'s Journey (2003)','Moribito: Guardian of the Spirit','The Twelve Kingdoms','Shirobako','Keep Your Hands Off Eizouken!','Girls Band Cry',
'Tokyo Godfathers','Millennium Actress','Paprika','Akira','Ghost in the Shell','Ghost in the Shell: Stand Alone Complex 2nd GIG','Puella Magi Madoka Magica','Puella Magi Madoka Magica the Movie: Rebellion','The First Slam Dunk','Blue Giant',
'Look Back','Suzume','Kiki\'s Delivery Service','My Neighbor Totoro','Castle in the Sky','Howl\'s Moving Castle','Porco Rosso','Whisper of the Heart','Only Yesterday','The Wind Rises',
'Delicious in Dungeon','Golden Kamuy','Land of the Lustrous','Ranking of Kings','Devilman Crybaby','Parasyte: The Maxim','Heavenly Delusion','Summer Time Rendering','The Promised Neverland','Baccano!',
'86 EIGHTY-SIX','Psycho-Pass','Black Lagoon','Hellsing Ultimate','Dorohedoro','Kaiji: Ultimate Survivor','Gintama','JoJo\'s Bizarre Adventure','One Piece','Dragon Ball',
'Space Brothers','Ashita no Joe','Cross Game','Nodame Cantabile','Kids on the Slope','Hikaru no Go','Run with the Wind','Cardcaptor Sakura','Rose of Versailles','Future Boy Conan',
'Mobile Suit Gundam','Mobile Suit Zeta Gundam','Turn A Gundam','Mobile Suit Gundam 00','Eureka Seven','The Vision of Escaflowne','Dennou Coil','Kaiba','Space Battleship Yamato 2199','Royal Space Force: The Wings of Honnêamise',
'Mind Game','The Night Is Short, Walk on Girl','Inu-Oh','Revue Starlight: The Movie','Kizumonogatari','Monogatari Series','Katanagatari','Sonny Boy','Heike Monogatari','Kyousougiga',
'Avatar: The Last Airbender','Pantheon','Scavengers Reign','Primal','KPop Demon Hunters','The Mitchells vs. the Machines','Puss in Boots: The Last Wish','The Legend of Korra','The Boondocks','Teen Titans',
'Witch Hat Atelier','Frieren: Beyond Journey\'s End Season 2','Steel Ball Run: JoJo\'s Bizarre Adventure','Dorohedoro Season 2','Daemons of the Shadow Realm','My Hero Academia FINAL SEASON','The Apothecary Diaries Season 2','Gachiakuta','Takopi\'s Original Sin','The Summer Hikaru Died',
]
priority={norm(t):i for i,t in enumerate(TOP_ORDER)}
# Ensure priority keys follow aliases.
for k in list(priority):
    if k in ALIASES:
        priority[norm(ALIASES[k])]=priority[k]

# Override broad content ratings for useful adult filters.
ADULT_OVERRIDES={
'Interspecies Reviewers':(5,5,1,0,1,['Ecchi','Erotic','Adult Only']),
'High School DxD':(4,5,3,1,2,['Ecchi','Adult Only']),
'Golden Boy':(4,4,1,0,1,['Ecchi','Adult Comedy']),
'Highschool of the Dead':(4,5,5,4,3,['Ecchi','Gore','Adult Only']),
'Rin: Daughters of Mnemosyne':(5,5,5,5,5,['Erotic','Extreme Violence','Gore','Adult Only']),
'Wicked City':(5,5,5,4,5,['Erotic','Extreme Violence','Adult Only']),
'Belladonna of Sadness':(5,5,4,2,5,['Erotic','Disturbing','Adult Only']),
'Lupin the Third: The Woman Called Fujiko Mine':(4,4,3,1,3,['Erotic','Adult Animation']),
'Cyberpunk: Edgerunners':(4,4,5,5,5,['Adult Animation','Gore']),
'Devilman Crybaby':(5,5,5,5,5,['Adult Animation','Erotic','Gore','Disturbing']),
'Hellsing Ultimate':(2,2,5,5,5,['Adult Animation','Gore','Extreme Violence']),
'Perfect Blue':(4,4,4,2,5,['Adult Animation','Disturbing']),
'Blue Eye Samurai':(4,4,5,4,4,['Adult Animation','Extreme Violence']),
'Castlevania':(4,4,5,5,4,['Adult Animation','Gore']),
'Castlevania: Nocturne':(3,3,5,5,4,['Adult Animation','Gore']),
'Love, Death + Robots':(5,5,5,5,5,['Adult Animation','Erotic','Gore']),
'Invincible':(2,2,5,5,4,['Adult Animation','Gore']),
'Primal':(1,2,5,5,4,['Adult Animation','Gore']),
'Twilight of the Gods':(5,5,5,5,4,['Adult Animation','Erotic','Gore']),
'Spawn':(3,3,5,5,5,['Adult Animation','Gore','Disturbing']),
'Todd McFarlane\'s Spawn':(3,3,5,5,5,['Adult Animation','Gore','Disturbing']),
'Mezzo Forte':(5,5,5,4,4,['Hentai','Erotic','Adult Only','Gore']),
'Words Worth':(5,5,4,3,5,['Hentai','Erotic','Adult Only','Disturbing']),
'Ogenki Clinic':(5,5,1,0,2,['Hentai','Erotic','Adult Comedy','Adult Only']),
'Fencer of Minerva':(5,5,4,2,5,['Hentai','Erotic','Adult Only','Disturbing']),
'Daiakuji: The Xena Buster':(5,5,5,3,5,['Hentai','Extreme Violence','Adult Only','Disturbing']),
}

items=list(entries.values())
# Normalized canonical dedupe one more time.
canon={}
for x in items:
    key=norm(x['title'])
    target=ALIASES.get(key)
    if target: key=norm(target); x['title']=target
    if key in canon:
        # keep better note/band
        cur=canon[key]
        if band_score.get(x.get('quality_band','B'),0)>band_score.get(cur.get('quality_band','B'),0): canon[key]=x
    else: canon[key]=x
items=list(canon.values())

reverse_aliases={}
for a,t in ALIASES.items(): reverse_aliases.setdefault(norm(t),[]).append(a)
for x in items:
    x['id']=slug_id(x['title'])
    x['aliases']=reverse_aliases.get(norm(x['title']),[])
    band=x.get('quality_band') or x.get('tier','A')
    x['tier']=band
    x['quality_band']=band
    # New content dimensions
    sex=max(0,min(5,round(x.get('explicitness',1)*0.7)))
    nudity=max(0,min(5,x.get('explicitness',1)))
    violence=max(0,min(5,x.get('darkness',2)+1 if any(g in x.get('genres','').lower() for g in ['action','war','horror','crime']) else x.get('darkness',2)))
    gore=max(0,min(5,x.get('darkness',2)-1 if any(g in x.get('genres','').lower() for g in ['horror','gore','dark fantasy']) else 0))
    disturbing=max(0,min(5,x.get('darkness',2)))
    tags=[]
    if x['title'] in ADULT_OVERRIDES:
        sex,nudity,violence,gore,disturbing,tags=ADULT_OVERRIDES[x['title']]
        adult_caveats={
            'Mezzo Forte':'Use the explicit original cut if you specifically want the hentai version; censored/non-explicit edits also circulate.',
            'Words Worth':'Contains coercive and disturbing sexual material; the recommendation is for viewers who knowingly want extreme adult animation.',
            'Ogenki Clinic':'Very broad, very dated sex comedy; included for comic energy rather than dramatic depth.',
            'Fencer of Minerva':'Sex slavery and coercive material are central to the setting; definitely not a light erotic fantasy.',
            'Daiakuji: The Xena Buster':'Exploitative and violent eroge material; included for its unusually plot-heavy action/crime structure.'
        }
        if x['title'] in adult_caveats: x['caveat']=adult_caveats[x['title']]
    elif any(w in x.get('genres','').lower() for w in ['ecchi','erotic','adult','sex comedy']): tags=['Adult Only']
    elif max(sex,nudity,gore)>=4: tags=['Adult Only']
    x['content']={'sex':sex,'nudity':nudity,'violence':violence,'gore':gore,'disturbing':disturbing,'tags':tags}
    # Emotional payoff is a first-class score, not a genre preference.
    emogen=x.get('genres','').lower()
    emotional=10 if any(w in emogen for w in ['drama','romance','coming-of-age','war']) and band=='S+' else (9 if any(w in emogen for w in ['drama','romance','coming-of-age']) else 7)
    x['scores']={
        'overall':100 if band=='S+' else (94 if band=='S' else 88 if band=='A+' else 82 if band=='A' else 76),
        'entertainment':x.get('entertainment',8),'production':x.get('production',8),'story':x.get('story',8),'emotional':emotional
    }

# Sort: explicit priority, then quality band, then previous rank/year/title.
def sortkey(x):
    p=priority.get(norm(x['title']),99999)
    if p<99999: return (0,p)
    bandrank={'S+':0,'S':1,'A+':2,'A':3,'B+':4,'B':5}.get(x.get('quality_band','A'),3)
    oldrank=x.get('rank',9999)
    return (1,bandrank,oldrank if oldrank<9999 else 9999, -(x.get('year') or 0), x['title'])
items.sort(key=sortkey)
for i,x in enumerate(items,1):
    x['rank']=i
    x.pop('curation_score',None)
    # clean legacy fields that the new UI no longer depends on but keep source/API.

# Collections: complete/curated, with Ghibli complete by official works page.
COLLECTIONS=[
{'id':'studio-ghibli','name':'Studio Ghibli','kind':'Studio','mode':'complete','description':'The complete 27-work official Studio Ghibli works list, including Nausicaä, On Your Mark and Ghiblies Episode 2.','titles':[
'The Boy and the Heron','Earwig and the Witch','The Red Turtle','When Marnie Was There','The Tale of the Princess Kaguya','The Wind Rises','From Up on Poppy Hill','Arrietty','Ponyo','Tales from Earthsea','Howl\'s Moving Castle','The Cat Returns','Ghiblies Episode 2','Spirited Away','My Neighbors the Yamadas','Princess Mononoke','Whisper of the Heart','On Your Mark','Pom Poko','Ocean Waves','Porco Rosso','Only Yesterday','Kiki\'s Delivery Service','My Neighbor Totoro','Grave of the Fireflies','Castle in the Sky','Nausicaä of the Valley of the Wind']},
{'id':'kyoto-animation','name':'Kyoto Animation','kind':'Studio','mode':'highlights','description':'Emotion, character acting and some of television anime\'s finest compositing.','titles':['Violet Evergarden','A Silent Voice','Sound! Euphonium','Liz and the Blue Bird','Hyouka','The Melancholy of Haruhi Suzumiya','The Disappearance of Haruhi Suzumiya','K-On!','Nichijou','Clannad / After Story','Tamako Love Story','Tsurune','Beyond the Boundary','CITY THE ANIMATION']},
{'id':'madhouse','name':'Madhouse','kind':'Studio','mode':'highlights','description':'Decades of prestige, genre range and animator-driven productions.','titles':['Perfect Blue','Monster','Death Note','Hunter x Hunter (2011)','One Punch Man','Parasyte: The Maxim','Frieren: Beyond Journey\'s End','Nana','Chihayafuru','Hajime no Ippo','Trigun Stampede / Stargaze','Black Lagoon','Redline','Cardcaptor Sakura','Claymore','Paprika']},
{'id':'mappa','name':'MAPPA','kind':'Studio','mode':'highlights','description':'Modern high-intensity studio work across action, drama and experimental originals.','titles':['Jujutsu Kaisen','Chainsaw Man','Vinland Saga','Attack on Titan','Dorohedoro','Dororo','Banana Fish','Terror in Resonance','Hell\'s Paradise','Lazarus','The Rose of Versailles (2025)','Ranma 1/2 (2024)','Jujutsu Kaisen Season 3']},
{'id':'bones','name':'Bones','kind':'Studio','mode':'highlights','description':'Character animation, action and long-running genre craftsmanship.','titles':['Fullmetal Alchemist: Brotherhood','Mob Psycho 100','My Hero Academia','Eureka Seven','Bungo Stray Dogs','Noragami','Soul Eater','Space Dandy','Darker than Black','Blood Blockade Battlefront','Super Crooks','My Hero Academia FINAL SEASON']},
{'id':'trigger-gainax','name':'GAINAX → Trigger','kind':'Studio lineage','mode':'highlights','description':'The maximalist lineage from Gainax experimentation to Trigger spectacle.','titles':['Neon Genesis Evangelion','Gunbuster','Royal Space Force: The Wings of Honnêamise','FLCL','Tengen Toppa Gurren Lagann','Panty & Stocking with Garterbelt','Kill la Kill','Little Witch Academia','Promare','Cyberpunk: Edgerunners','Delicious in Dungeon','SSSS.GRIDMAN','SSSS.DYNAZENON','Gridman Universe','New PANTY & STOCKING with GARTERBELT']},
{'id':'ufotable','name':'ufotable','kind':'Studio','mode':'highlights','description':'Digital compositing, effects-heavy action and premium franchise filmmaking.','titles':['Fate/Zero','Fate/stay night: Unlimited Blade Works','The Garden of Sinners','Demon Slayer: Kimetsu no Yaiba','Demon Slayer: Kimetsu no Yaiba Infinity Castle']},
{'id':'production-ig','name':'Production I.G','kind':'Studio','mode':'highlights','description':'Cyberpunk, sports and grounded action with a long technical legacy.','titles':['Ghost in the Shell','Ghost in the Shell: Stand Alone Complex','Ghost in the Shell: Stand Alone Complex 2nd GIG','Haikyu!!','Psycho-Pass','Kaiju No. 8','Heavenly Delusion','Moribito: Guardian of the Spirit','Run with the Wind','Jin-Roh: The Wolf Brigade']},
{'id':'science-saru','name':'Science SARU','kind':'Studio','mode':'highlights','description':'Loose movement, formal experimentation and director-forward productions.','titles':['DAN DA DAN','Devilman Crybaby','Keep Your Hands Off Eizouken!','Scott Pilgrim Takes Off','Inu-Oh','The Night Is Short, Walk on Girl','Lu Over the Wall','Ride Your Wave','The Heike Story']},
{'id':'wit-studio','name':'WIT Studio','kind':'Studio','mode':'highlights','description':'High-end action and adventurous production design.','titles':['Attack on Titan','Vinland Saga','Ranking of Kings','Great Pretender','Spy x Family','The Ancient Magus\' Bride','Kabaneri of the Iron Fortress']},
{'id':'shaft','name':'SHAFT','kind':'Studio','mode':'highlights','description':'Graphic composition, dialogue-driven direction and a very recognizable visual grammar.','titles':['Monogatari Series','Bakemonogatari','Kizumonogatari','Monogatari Series Second Season','Owarimonogatari','Puella Magi Madoka Magica','March Comes in Like a Lion','Sayonara, Zetsubou-Sensei','Kubikiri Cycle']},
{'id':'sunrise-bn','name':'Sunrise / Bandai Namco Filmworks','kind':'Studio','mode':'highlights','description':'Mecha, space opera and some of anime\'s most durable franchises.','titles':['Mobile Suit Gundam','Mobile Suit Zeta Gundam','Mobile Suit Gundam 0080: War in the Pocket','Mobile Suit Gundam: Char\'s Counterattack','Turn A Gundam','Mobile Suit Gundam 00','Mobile Suit Gundam Unicorn','Mobile Suit Gundam Thunderbolt','Mobile Suit Gundam: The Witch from Mercury','Code Geass','Cowboy Bebop','The Vision of Escaflowne','The Big O']},
{'id':'cloverworks','name':'CloverWorks','kind':'Studio','mode':'highlights','description':'Polished character animation across romance, comedy and action.','titles':['Bocchi the Rock!','Spy x Family','My Dress-Up Darling','Horimiya','Rascal Does Not Dream of Bunny Girl Senpai','WIND BREAKER','The Promised Neverland','The Elusive Samurai']},
{'id':'a1','name':'A-1 Pictures','kind':'Studio','mode':'highlights','description':'Mainstream range from romance to huge action productions.','titles':['Kaguya-sama: Love Is War','86 EIGHTY-SIX','Lycoris Recoil','Solo Leveling','Sword Art Online','ERASED','Your Lie in April','Anohana','Magi: The Labyrinth of Magic','Blue Exorcist','Shinsekai yori']},
{'id':'toei','name':'Toei Animation','kind':'Studio','mode':'highlights','description':'Foundational television anime and enduring mass-audience franchises.','titles':['Dragon Ball','Dragon Ball Z Kai','Dragon Ball Super','One Piece','Sailor Moon','Digimon Adventure','Mononoke','World Trigger','Slam Dunk','Galaxy Express 999','Fist of the North Star','Saint Seiya','HeartCatch PreCure!']},
{'id':'studio4c','name':'Studio 4°C','kind':'Studio','mode':'highlights','description':'Experimental features, anthologies and aggressively stylized animation.','titles':['Tekkonkinkreet','Mind Game','Children of the Sea','Mutafukaz','Genius Party','Genius Party Beyond','Berserk: The Golden Age Arc - Memorial Edition','The Animatrix']},
{'id':'pa-works','name':'P.A.WORKS','kind':'Studio','mode':'highlights','description':'Workplace drama, original series and emotionally direct features.','titles':['Shirobako','Maquia: When the Promised Flower Blooms','Ya Boy Kongming!','Skip and Loafer','Nagi-Asu: A Lull in the Sea','Angel Beats!','The Eccentric Family','Akiba Maid War','Buddy Daddies']},
{'id':'orange','name':'Orange','kind':'Studio','mode':'highlights','description':'The studio most responsible for proving character-driven CG anime can look fantastic.','titles':['Land of the Lustrous','Beastars','Trigun Stampede / Stargaze']},
{'id':'david','name':'David Production','kind':'Studio','mode':'highlights','description':'Bold color, sound and adaptation choices.','titles':['JoJo\'s Bizarre Adventure','Fire Force','Undead Unluck','Steel Ball Run: JoJo\'s Bizarre Adventure']},
{'id':'pierrot','name':'Pierrot','kind':'Studio','mode':'highlights','description':'Long-running shonen and several defining 80s-00s adaptations.','titles':['Naruto + Naruto Shippuden','Bleach + Thousand-Year Blood War','Yu Yu Hakusho','Great Teacher Onizuka','Yona of the Dawn']},
{'id':'tms','name':'TMS Entertainment','kind':'Studio','mode':'highlights','description':'Classic franchises and modern sports/drama hits.','titles':['Lupin III: The Castle of Cagliostro','Lupin III Part II','Fruits Basket (2019)','Megalo Box','Dr. STONE']},
{'id':'white-fox','name':'White Fox','kind':'Studio','mode':'highlights','description':'High-concept fantasy and time-loop drama.','titles':['Steins;Gate','Re:ZERO -Starting Life in Another World-','Katanagatari','Girls\' Last Tour','Goblin Slayer']},
{'id':'co-mix-wave','name':'CoMix Wave Films / Makoto Shinkai','kind':'Studio / director','mode':'highlights','description':'Shinkai\'s evolving visual language from tiny digital shorts to global theatrical blockbusters.','titles':['She and Her Cat','Voices of a Distant Star','The Place Promised in Our Early Days','5 Centimeters per Second','The Garden of Words','Your Name','Weathering With You','Suzume']},
{'id':'satoshi-kon','name':'Satoshi Kon','kind':'Director','mode':'complete','description':'Kon\'s feature filmography plus Paranoia Agent.','titles':['Perfect Blue','Millennium Actress','Tokyo Godfathers','Paranoia Agent','Paprika']},
{'id':'mamoru-hosoda','name':'Mamoru Hosoda','kind':'Director','mode':'highlights','description':'Digital worlds, family structures and kinetic feature animation.','titles':['The Girl Who Leapt Through Time','Summer Wars','Wolf Children','The Boy and the Beast','Mirai','Belle','Scarlet']},
{'id':'masaaki-yuasa','name':'Masaaki Yuasa','kind':'Director','mode':'highlights','description':'Elastic animation and formal invention across comedy, drama and music.','titles':['Mind Game','The Tatami Galaxy','Ping Pong the Animation','Devilman Crybaby','The Night Is Short, Walk on Girl','Lu Over the Wall','Ride Your Wave','Keep Your Hands Off Eizouken!','Inu-Oh']},
{'id':'watanabe','name':'Shinichiro Watanabe','kind':'Director','mode':'highlights','description':'Music-driven genre hybrids with some of anime\'s best action direction.','titles':['Macross Plus','Cowboy Bebop','Samurai Champloo','Kids on the Slope','Terror in Resonance','Carole & Tuesday','Lazarus']},
{'id':'mamoru-oshii','name':'Mamoru Oshii','kind':'Director','mode':'highlights','description':'Political, technological and philosophical animation with a singular sense of space.','titles':['Urusei Yatsura 2: Beautiful Dreamer','Angel\'s Egg','Patlabor: The Movie','Patlabor 2: The Movie','Ghost in the Shell','Ghost in the Shell 2: Innocence','Sky Crawlers']},
{'id':'naoko-yamada','name':'Naoko Yamada','kind':'Director','mode':'highlights','description':'Micro-gesture character direction, music and emotionally precise filmmaking.','titles':['K-On!','Tamako Love Story','A Silent Voice','Liz and the Blue Bird','Heike Monogatari','The Colors Within']},
]


# Additional major studio / international animation collections.
COLLECTIONS.extend([
{'id':'jcstaff','name':'J.C.STAFF','kind':'Studio','mode':'highlights','description':'A huge genre-spanning television catalog: romance, comedy, food battles, fantasy and some of the best Railgun material.','titles':['Toradora!','Revolutionary Girl Utena','Azumanga Daioh','Honey and Clover','Maid-Sama!','The Pet Girl of Sakurasou','A Certain Scientific Railgun','Food Wars! Shokugeki no Soma','Hi Score Girl','Flying Witch','Prison School','The Disastrous Life of Saiki K.','Is It Wrong to Try to Pick Up Girls in a Dungeon?','The Duke of Death and His Maid','Excel Saga']},
{'id':'studio-deen','name':'Studio DEEN','kind':'Studio','mode':'highlights','description':'A long-running studio whose strongest work ranges from classic comedy and horror to adult drama and BL romance.','titles':['Maison Ikkoku','Ranma 1/2 (1989)','You\'re Under Arrest','Read or Die OVA','GetBackers','Higurashi: When They Cry','KONOSUBA','Showa Genroku Rakugo Shinju','Sasaki and Miyano','Hell Girl']},
{'id':'kinema-citrus','name':'Kinema Citrus','kind':'Studio','mode':'highlights','description':'Dense fantasy worlds, tactile backgrounds and emotionally direct character animation.','titles':['Made in Abyss','Made in Abyss: Dawn of the Deep Soul','Made in Abyss: The Golden City of the Scorching Sun','Barakamon','Revue Starlight','Revue Starlight: The Movie','My Happy Marriage','The Rising of the Shield Hero']},
{'id':'brains-base','name':"Brain's Base",'kind':'Studio','mode':'highlights','description':'An unusually strong run of ensemble drama, supernatural stories and character-first adaptations.','titles':['Baccano!','Durarara!!',"Natsume's Book of Friends",'Princess Jellyfish','Mawaru Penguindrum','My Teen Romantic Comedy SNAFU','My Little Monster','Hotarubi no Mori e','In/Spectre','To Your Eternity']},
{'id':'satelight','name':'Satelight','kind':'Studio','mode':'highlights','description':'Music, mecha and maximalist science fiction are the studio\'s natural habitat.','titles':['Noein','Macross Frontier','Macross Delta','Aquarion EVOL','Symphogear','White Album 2','AKB0048','Log Horizon','Somali and the Forest Spirit','Fairy Tail']},
{'id':'polygon','name':'Polygon Pictures','kind':'Studio','mode':'highlights','description':'A major Japanese CG studio, strongest when architecture, machinery and hostile futures are part of the appeal.','titles':['Knights of Sidonia','Ajin: Demi-Human','BLAME!','Levius','Kaina of the Great Snow Sea','Pacific Rim: The Black']},
{'id':'olm','name':'OLM','kind':'Studio','mode':'highlights','description':'Far broader than Pokémon: sports, thrillers, comedy and several excellent modern adaptations sit in its catalog.','titles':['Berserk (1997)','Major','Inazuma Eleven','Utawarerumono','Odd Taxi','Summertime Rendering',"Komi Can't Communicate",'The Apothecary Diaries','The Apothecary Diaries Season 2']},
{'id':'doga-kobo','name':'Doga Kobo','kind':'Studio','mode':'highlights','description':'Character animation and comic timing, with recent work proving the studio can pivot into glossy high-stakes drama.','titles':["Monthly Girls' Nozaki-kun",'YuruYuri','New Game!','Gabriel DropOut','Plastic Memories','Sleepy Princess in the Demon Castle','Oshi no Ko']},
{'id':'silver-link','name':'SILVER LINK.','kind':'Studio','mode':'highlights','description':'A reliable home for colorful fantasy, comedy and character-driven television anime.','titles':['Non Non Biyori','Kokoro Connect','BOFURI','Chivalry of a Failed Knight','The Misfit of Demon King Academy','My Next Life as a Villainess','Restaurant to Another World','Tanaka-kun Is Always Listless','Dusk Maiden of Amnesia']},
{'id':'lidenfilms','name':'LIDENFILMS','kind':'Studio','mode':'highlights','description':'A broad modern catalog with especially good recent work in nocturnal romance, historical action and grounded drama.','titles':['Call of the Night','Blade of the Immortal (2019)','Insomniacs After School','Rurouni Kenshin (2023)','Tokyo Revengers','The Heroic Legend of Arslan','Terraformars','Cells at Work! Code Black']},
{'id':'troyca','name':'TROYCA','kind':'Studio','mode':'highlights','description':'Director-forward originals and polished adaptations with a taste for adult drama, mystery and clean digital compositing.','titles':['Re:Creators','Bloom Into You','Overtake!','IDOLiSH7',"Lord El-Melloi II's Case Files",'Aldnoah.Zero',"Beautiful Bones: Sakurako's Investigation"]},
{'id':'lerche','name':'Lerche','kind':'Studio','mode':'highlights','description':'Visually assertive comedy, romance and school stories, often with darker material hiding behind a bright surface.','titles':['Assassination Classroom',"Scum's Wish",'Given','School-Live!','Toilet-Bound Hanako-kun','Asobi Asobase','Monster Musume']},
{'id':'studio-colorido','name':'Studio Colorido','kind':'Studio','mode':'highlights','description':'Compact features and shorts built around expressive color, youth stories and unusually fluid movement.','titles':['Penguin Highway','A Whisker Away','Burn the Witch','Pokémon: Twilight Wings','Drifting Home']},
{'id':'passione','name':'Passione','kind':'Studio','mode':'highlights','description':'Ecchi, horror and fantasy handled with far more visual personality than the studio\'s niche reputation suggests.','titles':['Interspecies Reviewers','Mieruko-chan','Rokka: Braves of the Six Flowers','Citrus','Spice and Wolf: MERCHANT MEETS THE WISE WOLF']},
{'id':'sony-pictures-animation','name':'Sony Pictures Animation','kind':'Western studio','mode':'highlights','description':'One of the central studios behind the current stylized-CG revolution in mainstream Western feature animation.','titles':['Spider-Man: Into the Spider-Verse','Spider-Man: Across the Spider-Verse','KPop Demon Hunters','The Mitchells vs. the Machines']},
{'id':'powerhouse','name':'Powerhouse Animation','kind':'Western studio','mode':'highlights','description':'US adult/action animation with an openly anime-influenced visual vocabulary and excellent fight direction.','titles':['Castlevania','Castlevania: Nocturne','Blood of Zeus','Seis Manos','Tomb Raider: The Legend of Lara Croft','Masters of the Universe: Revelation','Masters of the Universe: Revolution']},
{'id':'studio-mir','name':'Studio Mir','kind':'Korean / international studio','mode':'highlights','description':'A key bridge between Korean production craft and high-end Western action animation.','titles':['The Legend of Korra',"DOTA: Dragon's Blood",'The Witcher: Nightmare of the Wolf','Voltron: Legendary Defender','Kipo and the Age of Wonderbeasts',"X-Men '97",'Lookism','Devil May Cry (2025)','My Adventures with Superman']},
{'id':'titmouse','name':'Titmouse','kind':'Western studio','mode':'highlights','description':'Adult serialized animation that ranges from cerebral sci-fi to fantasy comedy and alien ecology.','titles':['The Legend of Vox Machina','Pantheon','Scavengers Reign']},
{'id':'fortiche','name':'Fortiche Production','kind':'French animation studio','mode':'highlights','description':'Painterly 2D/3D hybrid animation and cinematic character acting; the studio that made Arcane a visual benchmark.','titles':['Arcane']},
{'id':'studio-ponoc','name':'Studio Ponoc','kind':'Studio','mode':'highlights','description':'A Ghibli-descended feature studio with lavish hand-drawn fantasy and emotionally direct short-form work.','titles':['The Imaginary',"Mary and The Witch's Flower",'Modest Heroes']},
])

# Add any collection-referenced titles missing from catalog as low-priority curated records.
bytitle={norm(x['title']):x for x in items}
for c in COLLECTIONS:
    for t in c['titles']:
        alias_target=ALIASES.get(norm(t),t)
        k=norm(alias_target)
        t=alias_target
        if k not in bytitle:
            rec={'title':t,'year':0,'type':'Series','origin':'Japan','genres':'Various','pace':'Varies','commitment':'Varies','entertainment':8,'production':8,'story':8,'darkness':2,'explicitness':1,'why':'Included through a curated studio/director collection.','editorial_note':'Included through a curated studio/director collection.','caveat':'','watch_note':'','api':'anilist','lookupTitle':t,'provisional':False,'fit_score':82,'tier':'A','quality_band':'A','sourceUrl':'https://anilist.co/search/anime?search='+re.sub(r'\s+','+',t),'content':{'sex':1,'nudity':1,'violence':2,'gore':0,'disturbing':2,'tags':[]},'scores':{'overall':82,'entertainment':8,'production':8,'story':8,'emotional':7},'id':slug_id(t)}
            items.append(rec);bytitle[k]=rec

# Re-sort after collection additions.
items.sort(key=sortkey)
for i,x in enumerate(items,1): x['rank']=i

# Resolve collection title IDs and keep missing names for transparency.
for c in COLLECTIONS:
    c['items']=[]
    for t in c.pop('titles'):
        alias_target=ALIASES.get(norm(t),t)
        x=bytitle.get(norm(alias_target))
        if x: c['items'].append(x['id'])

# Franchise guides. Steps can target titles or precise episode instructions.
FRANCHISES=[
{'id':'haruhi','name':'The Melancholy of Haruhi Suzumiya','summary':'The famous episode-order problem. First-timers can use 2009 chronological order, then The Disappearance.','orders':[
 {'label':'Recommended / 2009 chronological','note':'This interleaves the 2006 and 2009 material chronologically. Endless Eight is deliberately repetitive; all eight are listed, but an efficiency option is noted.','steps':[
  {'n':'01','title':'The Melancholy of Haruhi Suzumiya I','flag':'ESSENTIAL'}, {'n':'02','title':'The Melancholy of Haruhi Suzumiya II','flag':'ESSENTIAL'}, {'n':'03','title':'The Melancholy of Haruhi Suzumiya III','flag':'ESSENTIAL'}, {'n':'04','title':'The Melancholy of Haruhi Suzumiya IV','flag':'ESSENTIAL'}, {'n':'05','title':'The Melancholy of Haruhi Suzumiya V','flag':'ESSENTIAL'}, {'n':'06','title':'The Melancholy of Haruhi Suzumiya VI','flag':'ESSENTIAL'}, {'n':'07','title':'The Boredom of Haruhi Suzumiya','flag':'ESSENTIAL'}, {'n':'08','title':'Bamboo Leaf Rhapsody','flag':'ESSENTIAL'}, {'n':'09','title':'Mystérique Sign','flag':'ESSENTIAL'}, {'n':'10','title':'Remote Island Syndrome Part I','flag':'ESSENTIAL'}, {'n':'11','title':'Remote Island Syndrome Part II','flag':'ESSENTIAL'},
  {'n':'12','title':'Endless Eight I','flag':'ESSENTIAL'}, {'n':'13','title':'Endless Eight II','flag':'OPTIONAL','note':'Efficiency route: after I, you can jump to VIII if you do not want the full experiment.'}, {'n':'14','title':'Endless Eight III','flag':'OPTIONAL'}, {'n':'15','title':'Endless Eight IV','flag':'OPTIONAL'}, {'n':'16','title':'Endless Eight V','flag':'OPTIONAL'}, {'n':'17','title':'Endless Eight VI','flag':'OPTIONAL'}, {'n':'18','title':'Endless Eight VII','flag':'OPTIONAL'}, {'n':'19','title':'Endless Eight VIII','flag':'ESSENTIAL'},
  {'n':'20','title':'The Sigh of Haruhi Suzumiya I','flag':'ESSENTIAL'}, {'n':'21','title':'The Sigh of Haruhi Suzumiya II','flag':'ESSENTIAL'}, {'n':'22','title':'The Sigh of Haruhi Suzumiya III','flag':'ESSENTIAL'}, {'n':'23','title':'The Sigh of Haruhi Suzumiya IV','flag':'ESSENTIAL'}, {'n':'24','title':'The Sigh of Haruhi Suzumiya V','flag':'ESSENTIAL'}, {'n':'25','title':'The Adventures of Mikuru Asahina Episode 00','flag':'ESSENTIAL'}, {'n':'26','title':'Live Alive','flag':'ESSENTIAL'}, {'n':'27','title':'The Day of Sagittarius','flag':'ESSENTIAL'}, {'n':'28','title':'Someday in the Rain','flag':'ESSENTIAL'}, {'n':'FILM','title':'The Disappearance of Haruhi Suzumiya','flag':'ESSENTIAL'}]}]},
{'id':'monogatari','name':'Monogatari','summary':'Novel order is the cleanest first-time route. Chronological order is intentionally not recommended because the story uses withheld information.','orders':[{'label':'Recommended novel order','steps':[
 {'n':'1','title':'Bakemonogatari','flag':'ESSENTIAL'}, {'n':'2','title':'Kizumonogatari I-III','flag':'ESSENTIAL'}, {'n':'3','title':'Nisemonogatari','flag':'ESSENTIAL'}, {'n':'4','title':'Nekomonogatari (Black)','flag':'ESSENTIAL'}, {'n':'5','title':'Monogatari Series Second Season eps. 1-10','flag':'ESSENTIAL'}, {'n':'6','title':'Hanamonogatari','flag':'ESSENTIAL'}, {'n':'7','title':'Monogatari Series Second Season eps. 11-26','flag':'ESSENTIAL'}, {'n':'8','title':'Tsukimonogatari','flag':'ESSENTIAL'}, {'n':'9','title':'Koyomimonogatari','flag':'ESSENTIAL'}, {'n':'10','title':'Owarimonogatari','flag':'ESSENTIAL'}, {'n':'11','title':'Owarimonogatari Second Season','flag':'ESSENTIAL'}, {'n':'12','title':'Zoku Owarimonogatari','flag':'ESSENTIAL'}, {'n':'13','title':'Off & Monster Season','flag':'ESSENTIAL'}]}]},
{'id':'fate','name':'Fate / stay night core','summary':'There is no perfect spoiler-free order because Fate/Zero is a prequel written after the original routes.','orders':[
 {'label':'Best modern anime route','steps':[{'n':'1','title':'Fate/Zero','flag':'ESSENTIAL','note':'Chronological prequel; spoils some route reveals, but is an excellent entry.'},{'n':'2','title':'Fate/stay night: Unlimited Blade Works (2014)','flag':'ESSENTIAL'},{'n':'3','title':'Heaven\'s Feel I: presage flower','flag':'ESSENTIAL'},{'n':'4','title':'Heaven\'s Feel II: lost butterfly','flag':'ESSENTIAL'},{'n':'5','title':'Heaven\'s Feel III: spring song','flag':'ESSENTIAL'}]},
 {'label':'Spoiler-purist route','steps':[{'n':'1','title':'Unlimited Blade Works (2014)','flag':'ESSENTIAL'},{'n':'2','title':'Heaven\'s Feel trilogy','flag':'ESSENTIAL'},{'n':'3','title':'Fate/Zero','flag':'ESSENTIAL'}]}]},
{'id':'steins-gate','name':'Steins;Gate','summary':'The original series is the best first watch. Steins;Gate 0 branches from the alternate episode 23β.','orders':[
 {'label':'First watch','steps':[{'n':'1','title':'Steins;Gate episodes 1-24','flag':'ESSENTIAL'},{'n':'2','title':'Episode 25 / OVA','flag':'OPTIONAL'},{'n':'3','title':'Load Region of Déjà Vu movie','flag':'OPTIONAL'},{'n':'4','title':'Episode 23β - Divide by Zero','flag':'ESSENTIAL','note':'Watch only after finishing the original.'},{'n':'5','title':'Steins;Gate 0 episodes 1-23','flag':'ESSENTIAL'}]},
 {'label':'Branch chronology','steps':[{'n':'1','title':'Steins;Gate episodes 1-22','flag':'ESSENTIAL'},{'n':'2','title':'Episode 23β','flag':'ESSENTIAL'},{'n':'3','title':'Steins;Gate 0 episodes 1-23','flag':'ESSENTIAL'},{'n':'4','title':'Return to Steins;Gate episodes 23-24','flag':'ESSENTIAL'}]}]},
{'id':'gundam-uc','name':'Mobile Suit Gundam - Universal Century','summary':'The core political timeline. Release-ish order is better for first-time viewers; strict chronology puts prequels too early.','orders':[
 {'label':'Recommended first-time core','steps':[{'n':'1','title':'Mobile Suit Gundam (1979 TV or compilation films)','flag':'ESSENTIAL'},{'n':'2','title':'Mobile Suit Zeta Gundam','flag':'ESSENTIAL'},{'n':'3','title':'Mobile Suit Gundam ZZ','flag':'ESSENTIAL'},{'n':'4','title':'Char\'s Counterattack','flag':'ESSENTIAL'},{'n':'5','title':'0080: War in the Pocket','flag':'ESSENTIAL'},{'n':'6','title':'The 08th MS Team','flag':'ESSENTIAL'},{'n':'7','title':'0083: Stardust Memory','flag':'OPTIONAL'},{'n':'8','title':'The Origin','flag':'OPTIONAL','note':'Works better after you know the original cast.'},{'n':'9','title':'Gundam Unicorn','flag':'ESSENTIAL'},{'n':'10','title':'Gundam Narrative','flag':'OPTIONAL'},{'n':'11','title':'Hathaway','flag':'ESSENTIAL'},{'n':'12','title':'Gundam F91','flag':'OPTIONAL'},{'n':'13','title':'Victory Gundam','flag':'OPTIONAL'}]},
 {'label':'Internal chronology','steps':[{'n':'UC0068-0079','title':'The Origin','flag':'OPTIONAL'},{'n':'UC0079','title':'Mobile Suit Gundam','flag':'ESSENTIAL'},{'n':'UC0079','title':'The 08th MS Team','flag':'ESSENTIAL'},{'n':'UC0079-80','title':'0080: War in the Pocket','flag':'ESSENTIAL'},{'n':'UC0083','title':'0083: Stardust Memory','flag':'OPTIONAL'},{'n':'UC0087','title':'Zeta Gundam','flag':'ESSENTIAL'},{'n':'UC0088','title':'ZZ Gundam','flag':'ESSENTIAL'},{'n':'UC0093','title':'Char\'s Counterattack','flag':'ESSENTIAL'},{'n':'UC0096','title':'Unicorn','flag':'ESSENTIAL'},{'n':'UC0097','title':'Narrative','flag':'OPTIONAL'},{'n':'UC0105','title':'Hathaway','flag':'ESSENTIAL'},{'n':'UC0123','title':'F91','flag':'OPTIONAL'},{'n':'UC0153','title':'Victory Gundam','flag':'OPTIONAL'}]}]},
{'id':'gundam-standalone','name':'Gundam - standalone universes','summary':'These do not require Universal Century homework.','orders':[{'label':'Pick any entry','steps':[{'n':'A','title':'Iron-Blooded Orphans','flag':'ESSENTIAL'},{'n':'B','title':'The Witch from Mercury','flag':'ESSENTIAL'},{'n':'C','title':'Gundam 00','flag':'ESSENTIAL'},{'n':'D','title':'G Gundam','flag':'OPTIONAL'},{'n':'E','title':'Gundam SEED','flag':'OPTIONAL'},{'n':'F','title':'After War Gundam X','flag':'OPTIONAL'},{'n':'G','title':'Turn A Gundam','flag':'ESSENTIAL','note':'Standalone in practice, but richer after seeing older Gundam.'}]}]},
{'id':'evangelion','name':'Evangelion','summary':'Original continuity first; Rebuild is a separate reinterpretation that gains meaning from knowing it.','orders':[{'label':'Recommended','steps':[{'n':'1','title':'Neon Genesis Evangelion episodes 1-26','flag':'ESSENTIAL'},{'n':'2','title':'The End of Evangelion','flag':'ESSENTIAL'},{'n':'3','title':'Evangelion 1.11 You Are (Not) Alone','flag':'ESSENTIAL'},{'n':'4','title':'Evangelion 2.22 You Can (Not) Advance','flag':'ESSENTIAL'},{'n':'5','title':'Evangelion 3.33 You Can (Not) Redo','flag':'ESSENTIAL'},{'n':'6','title':'Evangelion 3.0+1.0 Thrice Upon a Time','flag':'ESSENTIAL'}]}]},
{'id':'ghost-shell','name':'Ghost in the Shell','summary':'Multiple separate continuities. Do not force them into one timeline.','orders':[
 {'label':'Oshii film continuity','steps':[{'n':'1','title':'Ghost in the Shell (1995)','flag':'ESSENTIAL'},{'n':'2','title':'Ghost in the Shell 2: Innocence','flag':'ESSENTIAL'}]},
 {'label':'Stand Alone Complex continuity','steps':[{'n':'1','title':'Stand Alone Complex','flag':'ESSENTIAL'},{'n':'2','title':'SAC 2nd GIG','flag':'ESSENTIAL'},{'n':'3','title':'Solid State Society','flag':'ESSENTIAL'},{'n':'4','title':'SAC_2045','flag':'OPTIONAL'}]},
 {'label':'Arise continuity','steps':[{'n':'1','title':'Arise Borders 1-4','flag':'OPTIONAL'},{'n':'2','title':'Pyrophoric Cult','flag':'OPTIONAL'},{'n':'3','title':'Ghost in the Shell: The New Movie','flag':'OPTIONAL'}]}]},
{'id':'berserk','name':'Berserk','summary':'Avoid the 2016-17 CG series. Pick 1997 or Memorial Edition for Golden Age, then continue in manga if you want the full story.','orders':[{'label':'Recommended animation route','steps':[{'n':'1','title':'Berserk (1997)','flag':'ESSENTIAL'},{'n':'ALT','title':'OR Golden Age Memorial Edition','flag':'ESSENTIAL'},{'n':'2','title':'Continue with manga from the beginning / post-Golden-Age','flag':'ESSENTIAL'},{'n':'SKIP','title':'Berserk (2016-2017)','flag':'SKIP'}]}]},
{'id':'jojo','name':'JoJo\'s Bizarre Adventure','summary':'Straightforward part order.','orders':[{'label':'Release / story order','steps':[{'n':'1','title':'Phantom Blood','flag':'ESSENTIAL'},{'n':'2','title':'Battle Tendency','flag':'ESSENTIAL'},{'n':'3','title':'Stardust Crusaders','flag':'ESSENTIAL'},{'n':'4','title':'Diamond Is Unbreakable','flag':'ESSENTIAL'},{'n':'5','title':'Golden Wind','flag':'ESSENTIAL'},{'n':'6','title':'Stone Ocean','flag':'ESSENTIAL'},{'n':'7','title':'Steel Ball Run','flag':'ESSENTIAL'}]}]},
{'id':'dragon-ball','name':'Dragon Ball','summary':'Kai is the efficient route through Z.','orders':[{'label':'Recommended','steps':[{'n':'1','title':'Dragon Ball','flag':'ESSENTIAL'},{'n':'2','title':'Dragon Ball Z Kai','flag':'ESSENTIAL'},{'n':'3','title':'Dragon Ball Super','flag':'ESSENTIAL'},{'n':'4','title':'Dragon Ball Super: Broly','flag':'ESSENTIAL'},{'n':'5','title':'Dragon Ball Super: Super Hero','flag':'ESSENTIAL'},{'n':'ALT','title':'Dragon Ball GT','flag':'OPTIONAL','note':'Separate non-Super sequel continuity.'}]}]},
{'id':'naruto','name':'Naruto','summary':'The canon story is excellent; the television run has a very large filler burden.','orders':[{'label':'Main route','steps':[{'n':'1','title':'Naruto','flag':'ESSENTIAL','note':'Use a filler guide aggressively, especially late in the original run.'},{'n':'2','title':'Naruto Shippuden','flag':'ESSENTIAL','note':'Again use a filler guide; do not treat filler as required continuity.'},{'n':'3','title':'The Last: Naruto the Movie','flag':'ESSENTIAL','note':'Watch after Shippuden episode 493 / before the final wedding stretch.'},{'n':'4','title':'Boruto','flag':'OPTIONAL'}]}]},
{'id':'bleach','name':'Bleach','summary':'Original TV plus Thousand-Year Blood War.','orders':[{'label':'Recommended','steps':[{'n':'1','title':'Bleach original series','flag':'ESSENTIAL','note':'Skip anime-original filler arcs unless curious.'},{'n':'2','title':'Thousand-Year Blood War Part 1','flag':'ESSENTIAL'},{'n':'3','title':'TYBW Part 2 - The Separation','flag':'ESSENTIAL'},{'n':'4','title':'TYBW Part 3 - The Conflict','flag':'ESSENTIAL'},{'n':'5','title':'TYBW final cour','flag':'ESSENTIAL'}]}]},
{'id':'one-piece','name':'One Piece','summary':'One continuous main story. Movies are optional; pacing is the main issue rather than continuity.','orders':[{'label':'Main route','steps':[{'n':'1','title':'One Piece TV from episode 1','flag':'ESSENTIAL','note':'Use the official anime or a reputable filler/pacing guide; do not skip canon arcs for chronology.'},{'n':'SPECIAL','title':'One Piece Fan Letter','flag':'OPTIONAL','note':'Best after you know the world/cast; it contains broad franchise context.'},{'n':'FILMS','title':'Theatrical films','flag':'OPTIONAL','note':'Mostly standalone/non-canon; Film Z, Gold, Stampede and Red are the major modern spectacle picks.'}]}]},
{'id':'demon-slayer','name':'Demon Slayer','summary':'Film/TV duplication exists around Mugen Train. Pick one version.','orders':[{'label':'Recommended','steps':[{'n':'1','title':'Season 1','flag':'ESSENTIAL'},{'n':'2','title':'Mugen Train film OR Mugen Train TV arc','flag':'ESSENTIAL','note':'Do not need both.'},{'n':'3','title':'Entertainment District Arc','flag':'ESSENTIAL'},{'n':'4','title':'Swordsmith Village Arc','flag':'ESSENTIAL'},{'n':'5','title':'Hashira Training Arc','flag':'ESSENTIAL'},{'n':'6','title':'Infinity Castle film trilogy','flag':'ESSENTIAL'}]}]},
{'id':'made-in-abyss','name':'Made in Abyss','summary':'One movie is mandatory; the recap films are not.','orders':[{'label':'Recommended','steps':[{'n':'1','title':'Season 1','flag':'ESSENTIAL'},{'n':'SKIP','title':'Journey\'s Dawn / Wandering Twilight recap films','flag':'SKIP'},{'n':'2','title':'Dawn of the Deep Soul','flag':'ESSENTIAL'},{'n':'3','title':'Season 2: The Golden City of the Scorching Sun','flag':'ESSENTIAL'}]}]},
{'id':'madoka','name':'Puella Magi Madoka Magica','summary':'TV series then Rebellion; recap films are optional.','orders':[{'label':'Recommended','steps':[{'n':'1','title':'Puella Magi Madoka Magica episodes 1-12','flag':'ESSENTIAL'},{'n':'SKIP','title':'Beginnings / Eternal recap films','flag':'OPTIONAL'},{'n':'2','title':'Rebellion','flag':'ESSENTIAL'},{'n':'3','title':'Walpurgisnacht: Rising','flag':'ESSENTIAL','note':'Continue once released/available in your region.'}]}]},
{'id':'macross','name':'Macross','summary':'Shared history, but several entries can be enjoyed independently.','orders':[{'label':'Core chronological-ish route','steps':[{'n':'1','title':'Super Dimension Fortress Macross','flag':'ESSENTIAL'},{'n':'ALT','title':'Do You Remember Love?','flag':'ESSENTIAL','note':'Film retelling/alternate version, worth seeing even after TV.'},{'n':'2','title':'Macross Plus','flag':'ESSENTIAL'},{'n':'3','title':'Macross 7','flag':'OPTIONAL'},{'n':'4','title':'Macross Zero','flag':'OPTIONAL','note':'Prequel, but better after some franchise context.'},{'n':'5','title':'Macross Frontier','flag':'ESSENTIAL'},{'n':'6','title':'Macross Delta','flag':'OPTIONAL'}]}]},
{'id':'fullmetal','name':'Fullmetal Alchemist','summary':'2003 and Brotherhood are separate adaptations. Neither is a season of the other.','orders':[
 {'label':'Brotherhood route','steps':[{'n':'1','title':'Fullmetal Alchemist: Brotherhood','flag':'ESSENTIAL'},{'n':'2','title':'The Sacred Star of Milos','flag':'OPTIONAL'}]},
 {'label':'2003 alternate continuity','steps':[{'n':'1','title':'Fullmetal Alchemist (2003)','flag':'ESSENTIAL'},{'n':'2','title':'Conqueror of Shamballa','flag':'ESSENTIAL'}]}]},
{'id':'higurashi','name':'Higurashi / When They Cry','summary':'Do not start with Gou even though it initially looks like a remake.','orders':[{'label':'Recommended','steps':[{'n':'1','title':'Higurashi no Naku Koro ni (2006)','flag':'ESSENTIAL'},{'n':'2','title':'Higurashi Kai','flag':'ESSENTIAL'},{'n':'3','title':'Higurashi Rei','flag':'OPTIONAL'},{'n':'4','title':'Higurashi Gou','flag':'OPTIONAL','note':'Sequel, not beginner remake.'},{'n':'5','title':'Higurashi Sotsu','flag':'OPTIONAL'}]}]},
{'id':'trigun','name':'Trigun','summary':'Original and Stampede/Stargaze are separate interpretations.','orders':[
 {'label':'Modern continuity','steps':[{'n':'1','title':'Trigun Stampede','flag':'ESSENTIAL'},{'n':'2','title':'Trigun Stargaze','flag':'ESSENTIAL'}]},
 {'label':'Original continuity','steps':[{'n':'1','title':'Trigun (1998)','flag':'ESSENTIAL'},{'n':'2','title':'Badlands Rumble','flag':'OPTIONAL'}]}]},
{'id':'castlevania','name':'Castlevania','summary':'Nocturne is a later-generation sequel continuity.','orders':[{'label':'Recommended','steps':[{'n':'1','title':'Castlevania seasons 1-4','flag':'ESSENTIAL'},{'n':'2','title':'Castlevania: Nocturne','flag':'ESSENTIAL'}]}]},
{'id':'psycho-pass','name':'Psycho-Pass','summary':'Season 1 is the masterpiece, but the later continuity is navigable.','orders':[{'label':'Chronological release','steps':[{'n':'1','title':'Psycho-Pass Season 1','flag':'ESSENTIAL'},{'n':'2','title':'Psycho-Pass 2','flag':'OPTIONAL'},{'n':'3','title':'Psycho-Pass: The Movie','flag':'ESSENTIAL'},{'n':'4','title':'Sinners of the System Case 1-3','flag':'OPTIONAL'},{'n':'5','title':'Psycho-Pass 3','flag':'ESSENTIAL'},{'n':'6','title':'First Inspector','flag':'ESSENTIAL'},{'n':'7','title':'Providence','flag':'ESSENTIAL','note':'Release-later prequel material; best after Season 3 context.'}]}]},
{'id':'gridman','name':'GRIDMAN Universe','summary':'Two TV series converge in the movie.','orders':[{'label':'Recommended','steps':[{'n':'1','title':'SSSS.GRIDMAN','flag':'ESSENTIAL'},{'n':'2','title':'SSSS.DYNAZENON','flag':'ESSENTIAL'},{'n':'3','title':'Gridman Universe','flag':'ESSENTIAL'}]}]},
{'id':'avatar','name':'Avatar animated universe','summary':'Straight chronological generations.','orders':[{'label':'Recommended','steps':[{'n':'1','title':'Avatar: The Last Airbender Books 1-3','flag':'ESSENTIAL'},{'n':'2','title':'The Legend of Korra Books 1-4','flag':'ESSENTIAL'}]}]},
{'id':'spider-verse','name':'Spider-Verse','summary':'Feature continuity.','orders':[{'label':'Release / story order','steps':[{'n':'1','title':'Spider-Man: Into the Spider-Verse','flag':'ESSENTIAL'},{'n':'2','title':'Spider-Man: Across the Spider-Verse','flag':'ESSENTIAL'},{'n':'3','title':'Spider-Man: Beyond the Spider-Verse','flag':'ESSENTIAL','note':'Watch when released.'}]}]},
]


FRANCHISES.extend([
{'id':'violet-evergarden','name':'Violet Evergarden','summary':'Release order works, but the Extra Episode has a precise chronological slot between TV episodes 4 and 5.','orders':[
 {'label':'Recommended chronological','steps':[{'n':'1','title':'Violet Evergarden TV episodes 1-4','flag':'ESSENTIAL'},{'n':'2','title':'Violet Evergarden Special / Extra Episode','flag':'ESSENTIAL','note':'Chronologically between TV episodes 4 and 5.'},{'n':'3','title':'Violet Evergarden TV episodes 5-13','flag':'ESSENTIAL'},{'n':'4','title':'Eternity and the Auto Memory Doll','flag':'ESSENTIAL'},{'n':'5','title':'Violet Evergarden: The Movie','flag':'ESSENTIAL'}]}]},
{'id':'attack-on-titan','name':'Attack on Titan','summary':'The main television story is linear; the OVAs are optional side material and are safest once the relevant characters have been introduced.','orders':[
 {'label':'Main story','steps':[{'n':'1','title':'Season 1 episodes 1-25','flag':'ESSENTIAL'},{'n':'2','title':'Season 2 episodes 26-37','flag':'ESSENTIAL'},{'n':'3','title':'Season 3 Part 1 episodes 38-49','flag':'ESSENTIAL'},{'n':'4','title':'Season 3 Part 2 episodes 50-59','flag':'ESSENTIAL'},{'n':'5','title':'The Final Season Part 1 episodes 60-75','flag':'ESSENTIAL'},{'n':'6','title':'The Final Season Part 2 episodes 76-87','flag':'ESSENTIAL'},{'n':'7','title':'The Final Chapters Special 1','flag':'ESSENTIAL'},{'n':'8','title':'The Final Chapters Special 2','flag':'ESSENTIAL'}]},
 {'label':'OVA placement without breaking momentum','steps':[{'n':'AFTER S1','title':"Ilse's Notebook / A Sudden Visitor / Distress",'flag':'OPTIONAL'},{'n':'AFTER S1','title':'No Regrets Parts 1-2','flag':'OPTIONAL','note':'Levi prequel; better once you know him.'},{'n':'AFTER S2','title':'Lost Girls Parts 1-3','flag':'OPTIONAL'}]}]},
{'id':'code-geass','name':'Code Geass','summary':'The original TV ending and the recap-film continuity are not exactly the same timeline. Resurrection follows the films.','orders':[
 {'label':'Original TV continuity','steps':[{'n':'1','title':'Code Geass: Lelouch of the Rebellion','flag':'ESSENTIAL'},{'n':'2','title':'Code Geass R2','flag':'ESSENTIAL'}]},
 {'label':'Movie / sequel continuity','steps':[{'n':'1','title':'Initiation recap film','flag':'OPTIONAL'},{'n':'2','title':'Transgression recap film','flag':'OPTIONAL'},{'n':'3','title':'Glorification recap film','flag':'OPTIONAL'},{'n':'4','title':'Lelouch of the Re;surrection','flag':'ESSENTIAL','note':'This sequel follows the recap-film changes, not the exact TV ending.'},{'n':'5','title':'Rozé of the Recapture','flag':'OPTIONAL'}]}]},
{'id':'hellsing','name':'Hellsing','summary':'Ultimate is the complete manga-faithful route. The 2001 TV series becomes its own story.','orders':[
 {'label':'Recommended','steps':[{'n':'1','title':'Hellsing Ultimate I-X','flag':'ESSENTIAL'}]},
 {'label':'Alternate adaptation','steps':[{'n':'ALT','title':'Hellsing (2001) episodes 1-13','flag':'OPTIONAL','note':'Interesting atmosphere and music, but increasingly anime-original.'}]}]},
{'id':'lotgh','name':'Legend of the Galactic Heroes','summary':'The classic OVA and Die Neue These are separate adaptations. The two classic films make a particularly clean entrance into the OVA.','orders':[
 {'label':'Classic OVA - recommended','steps':[{'n':'1','title':'My Conquest Is the Sea of Stars','flag':'ESSENTIAL'},{'n':'2','title':'Overture to a New War','flag':'ESSENTIAL','note':'Expanded retelling of the OVA opening; after this start the main OVA at episode 3.'},{'n':'3','title':'Legend of the Galactic Heroes OVA episodes 3-110','flag':'ESSENTIAL'},{'n':'4','title':'Gaiden prequel stories','flag':'OPTIONAL','note':'Chronologically earlier, but better after the main story.'}]},
 {'label':'Modern alternate adaptation','steps':[{'n':'ALT','title':'Legend of the Galactic Heroes: Die Neue These','flag':'ESSENTIAL'}]}]},
{'id':'blue-exorcist','name':'Blue Exorcist','summary':'Season 1 diverges into an anime-original ending. For a clean canon route, jump away before those episodes.','orders':[
 {'label':'Canon-first route','steps':[{'n':'1','title':'Blue Exorcist Season 1 episodes 1-17','flag':'ESSENTIAL'},{'n':'SKIP','title':'Season 1 episodes 18-25','flag':'SKIP','note':'Anime-original continuity; later canon seasons ignore it.'},{'n':'2','title':'Kyoto Saga','flag':'ESSENTIAL'},{'n':'3','title':'Shimane Illuminati Saga','flag':'ESSENTIAL'},{'n':'4','title':'Beyond the Snow Saga','flag':'ESSENTIAL'},{'n':'5','title':'The Blue Night Saga','flag':'ESSENTIAL'},{'n':'SIDE','title':'Blue Exorcist: The Movie','flag':'OPTIONAL'}]}]},
{'id':'black-butler','name':'Black Butler','summary':'The early anime contains major anime-original blocks. The manga-canon route requires explicit episode jumps.','orders':[
 {'label':'Manga-canon route','steps':[{'n':'1','title':'Black Butler Season 1 episodes 1-6','flag':'ESSENTIAL'},{'n':'SKIP','title':'Season 1 episodes 7-12','flag':'SKIP'},{'n':'2','title':'Season 1 episodes 13-15','flag':'ESSENTIAL','note':'Episode 15 contains some anime-original material near the end, but this is the relevant adapted arc.'},{'n':'SKIP','title':'Season 1 episodes 16-24 + all of Black Butler II','flag':'SKIP'},{'n':'3','title':'Book of Circus','flag':'ESSENTIAL'},{'n':'4','title':'Book of Murder Parts 1-2','flag':'ESSENTIAL'},{'n':'5','title':'Book of the Atlantic','flag':'ESSENTIAL'},{'n':'6','title':'Public School Arc','flag':'ESSENTIAL'},{'n':'7','title':'Emerald Witch Arc','flag':'ESSENTIAL'}]}]},
{'id':'promised-neverland','name':'The Promised Neverland','summary':'Season 1 is excellent. The second anime season compresses and removes too much material to be the recommended continuation.','orders':[
 {'label':'Recommended','steps':[{'n':'1','title':'The Promised Neverland Season 1 episodes 1-12','flag':'ESSENTIAL'},{'n':'2','title':'Continue with the manga from chapter 38','flag':'ESSENTIAL'},{'n':'SKIP','title':'The Promised Neverland Season 2','flag':'SKIP','note':'Watch only out of curiosity after knowing what was cut.'}]}]},
{'id':'garden-of-sinners','name':'The Garden of Sinners / Kara no Kyoukai','summary':'The movies are intentionally nonlinear. First-time viewers should use release order rather than trying to repair the chronology.','orders':[
 {'label':'Recommended release order','steps':[{'n':'1','title':'Overlooking View','flag':'ESSENTIAL'},{'n':'2','title':'A Study in Murder - Part 1','flag':'ESSENTIAL'},{'n':'3','title':'Remaining Sense of Pain','flag':'ESSENTIAL'},{'n':'4','title':'The Hollow Shrine','flag':'ESSENTIAL'},{'n':'5','title':'Paradox Spiral','flag':'ESSENTIAL'},{'n':'6','title':'Oblivion Recording','flag':'ESSENTIAL'},{'n':'7','title':'A Study in Murder - Part 2','flag':'ESSENTIAL'},{'n':'8','title':'Epilogue','flag':'ESSENTIAL'},{'n':'9','title':'Future Gospel','flag':'ESSENTIAL'},{'n':'10','title':'Future Gospel - Extra Chorus','flag':'OPTIONAL'}]}]},
{'id':'sword-art-online','name':'Sword Art Online','summary':'Progressive is a parallel Aincrad retelling, not the next season. Ordinal Scale belongs between SAO II and Alicization.','orders':[
 {'label':'Main anime route','steps':[{'n':'1','title':'Sword Art Online','flag':'ESSENTIAL'},{'n':'SIDE','title':'Extra Edition','flag':'OPTIONAL'},{'n':'2','title':'Sword Art Online II','flag':'ESSENTIAL'},{'n':'3','title':'Ordinal Scale','flag':'ESSENTIAL'},{'n':'4','title':'Alicization','flag':'ESSENTIAL'},{'n':'5','title':'Alicization - War of Underworld','flag':'ESSENTIAL'}]},
 {'label':'Aincrad alternate retelling','steps':[{'n':'ALT 1','title':'Progressive: Aria of a Starless Night','flag':'OPTIONAL'},{'n':'ALT 2','title':'Progressive: Scherzo of Deep Night','flag':'OPTIONAL'}]}]},
{'id':'rezero','name':'Re:ZERO','summary':'The Director\'s Cut can replace the original first season; do not watch both unless you want comparisons.','orders':[
 {'label':'Recommended','steps':[{'n':'1','title':'Season 1 OR Director\'s Cut','flag':'ESSENTIAL'},{'n':'SIDE','title':'Memory Snow','flag':'OPTIONAL'},{'n':'SIDE','title':'The Frozen Bond','flag':'ESSENTIAL','note':'Prequel material, best after meeting Emilia and Puck.'},{'n':'2','title':'Season 2 Part 1','flag':'ESSENTIAL'},{'n':'3','title':'Season 2 Part 2','flag':'ESSENTIAL'},{'n':'4','title':'Season 3','flag':'ESSENTIAL'}]}]},
{'id':'mushoku-tensei','name':'Mushoku Tensei','summary':'Mostly linear; the Eris OVA fills a gap inside the first season but works well immediately after it.','orders':[
 {'label':'Recommended','steps':[{'n':'1','title':'Season 1 Part 1','flag':'ESSENTIAL'},{'n':'2','title':'Season 1 Part 2','flag':'ESSENTIAL'},{'n':'SIDE','title':'Eris the Goblin Slayer OVA','flag':'ESSENTIAL','note':'Takes place during the first-season journey; watch after Season 1 to preserve flow.'},{'n':'3','title':'Season 2 Part 1','flag':'ESSENTIAL'},{'n':'4','title':'Season 2 Part 2','flag':'ESSENTIAL'}]}]},
{'id':'konosuba','name':'KONOSUBA','summary':'The Megumin spinoff is chronologically earlier, but it plays better after you already know the main cast.','orders':[
 {'label':'Recommended first watch','steps':[{'n':'1','title':'KONOSUBA Season 1','flag':'ESSENTIAL'},{'n':'2','title':'KONOSUBA Season 2','flag':'ESSENTIAL'},{'n':'3','title':'Legend of Crimson movie','flag':'ESSENTIAL'},{'n':'4','title':'An Explosion on This Wonderful World!','flag':'OPTIONAL','note':'Megumin prequel.'},{'n':'5','title':'KONOSUBA Season 3','flag':'ESSENTIAL'}]}]},
{'id':'clannad','name':'Clannad','summary':'After Story is the main continuation. The Tomoyo and Kyou chapters are alternate-route bonus episodes, not branches you need to splice into the main continuity.','orders':[
 {'label':'Main route','steps':[{'n':'1','title':'Clannad episodes 1-22','flag':'ESSENTIAL'},{'n':'2','title':'Clannad: After Story episodes 1-22','flag':'ESSENTIAL'},{'n':'3','title':'After Story episode 23 + recap/bonus material','flag':'OPTIONAL'}]},
 {'label':'Alternate-route extras','steps':[{'n':'ALT','title':'Tomoyo Chapter','flag':'OPTIONAL'},{'n':'ALT','title':'Kyou Chapter','flag':'OPTIONAL'}]}]},
{'id':'fruits-basket','name':'Fruits Basket (2019)','summary':'The 2019 adaptation is one continuous complete route. Prelude is best left until the ending is known.','orders':[
 {'label':'Recommended','steps':[{'n':'1','title':'Fruits Basket (2019) Season 1','flag':'ESSENTIAL'},{'n':'2','title':'Season 2','flag':'ESSENTIAL'},{'n':'3','title':'The Final','flag':'ESSENTIAL'},{'n':'4','title':'Fruits Basket: Prelude','flag':'OPTIONAL','note':'Contains recap plus additional prequel/epilogue material; safest after The Final.'}]}]},
{'id':'rurouni-kenshin','name':'Rurouni Kenshin','summary':'The 1996 series and 2023 remake are separate adaptations. Trust & Betrayal is an acclaimed prequel OVA that works after you know Kenshin.','orders':[
 {'label':'1996 classic route','steps':[{'n':'1','title':'Rurouni Kenshin (1996) episodes 1-62','flag':'ESSENTIAL','note':'Covers the essential Tokyo + Kyoto material.'},{'n':'SKIP','title':'Later 1996 TV filler','flag':'OPTIONAL'},{'n':'2','title':'Trust & Betrayal OVA','flag':'ESSENTIAL'},{'n':'3','title':'Reflection OVA','flag':'OPTIONAL','note':'Anime-original and controversial as an ending.'}]},
 {'label':'Modern remake route','steps':[{'n':'1','title':'Rurouni Kenshin (2023)','flag':'ESSENTIAL'},{'n':'2','title':'Kyoto Disturbance continuation','flag':'ESSENTIAL'}]}]},
{'id':'raildex','name':'A Certain Magical Index / Railgun','summary':'The franchise overlaps in time. For a first watch, a block order is easier and preserves reveals better than an obsessive scene-by-scene chronology.','orders':[
 {'label':'Recommended crossover order','steps':[{'n':'1','title':'A Certain Magical Index Season 1','flag':'ESSENTIAL'},{'n':'2','title':'A Certain Scientific Railgun','flag':'ESSENTIAL'},{'n':'3','title':'A Certain Scientific Railgun S','flag':'ESSENTIAL','note':'Its Sisters arc gives the most detailed version of events that overlap Index.'},{'n':'4','title':'A Certain Magical Index II','flag':'ESSENTIAL'},{'n':'5','title':'The Miracle of Endymion movie','flag':'OPTIONAL'},{'n':'6','title':'A Certain Scientific Railgun T','flag':'ESSENTIAL'},{'n':'7','title':'A Certain Magical Index III','flag':'OPTIONAL'},{'n':'SIDE','title':'A Certain Scientific Accelerator','flag':'OPTIONAL'}]}]},
])

# Reference sources embedded in the build for transparency.
SOURCES=[
 {'label':'Studio Ghibli official works list','url':'https://www.ghibli.jp/works/?OpBrower=1'},
 {'label':'Crunchyroll Anime Awards 2026 winners','url':'https://www.crunchyroll.com/news/latest/2026/5/22/anime-awards-2026-winners-list'},
 {'label':'Netflix adult animation catalog reference','url':'https://www.netflix.com/browse/genre/11881'},
 {'label':'Time Out - Best anime of 2026 so far','url':'https://www.timeout.com/film/the-best-animes-so-far'},
 {'label':'Sony Pictures Animation official projects','url':'https://www.sonypicturesanimation.com/projects'},
 {'label':'Powerhouse Animation official work archive','url':'https://www.powerhouseanimation.com/our-work/'},
 {'label':'Fortiche Production official projects','url':'https://forticheprod.com/fortichize/'},
 {'label':'OLM Group official works','url':'https://www.olm.co.jp/works?lang=en'},
 {'label':'Studio Ponoc official works','url':'https://www.ponoc.jp/works/'},
 {'label':'Doga Kobo official animation catalog','url':'https://www.dogakobo.com/en/animation/'},
 {'label':'Blue Exorcist watch order - Crunchyroll','url':'https://www.crunchyroll.com/news/guides/2025/3/17/how-to-watch-blue-exorcist-in-order'},
 {'label':'Black Butler watch order - Crunchyroll','url':'https://www.crunchyroll.com/news/guides/how-to-watch-black-butler-in-order'},
]

PUBLIC_NOTE_REWRITES={
 'Spirited Away':{'caveat':''},
 'The Apothecary Diaries':{'caveat':''},
 'Ghost in the Shell: Stand Alone Complex':{'caveat':'Dialogue-heavy and procedural.'},
 'Oshi no Ko':{'caveat':''},
 'The Summer Hikaru Died':{'caveat':'Deliberately slow and intimate.'},
 'Scott Pilgrim Takes Off':{'caveat':''},
 'Rurouni Kenshin: Trust & Betrayal':{'caveat':''},
 'Dead Dead Demons Dededede Destruction':{'caveat':'Character-driven and deliberately patient.'},
 'Daiakuji: The Xena Buster':{'caveat':'Contains graphic sexual material, violence and disturbing themes.'},
 'Words Worth':{'caveat':'Contains coercive and disturbing sexual material.'},
 'Ogenki Clinic':{'caveat':'Very broad, very dated adult comedy.'},
 "Frieren: Beyond Journey's End":{'caveat':'Deliberately reflective and patient, especially between major arcs.'},
 'Monster':{'caveat':'A true slow burn; the tension builds gradually over a long runtime.'},
 'Planetes':{'caveat':'The workplace setup takes time before the larger story opens up.'},
 'Fate/stay night: Unlimited Blade Works':{'watch_note':"Recommended route: Fate/Zero -> Unlimited Blade Works -> Heaven's Feel."},
 'Tomb Raider: The Legend of Lara Croft':{'caveat':'Solid rather than essential, but brisk and consistently entertaining.'},
 'Gungrave':{'caveat':'Episode 1 reveals later material; some viewers prefer starting at episode 2 and returning to it afterward.'},
 'Tokyo Ghoul':{'caveat':'Adaptation quality drops sharply after the first season. The manga is the better route for the full story.'},
 'Dragon Ball Z Kai':{'watch_note':'For the full beginning, watch the original Dragon Ball first; Kai is the streamlined Z-era route.'},
 'Mezzo Forte':{'caveat':'The explicit original cut and censored/non-explicit edits both circulate.'},
}
public_items=[]
for item in items:
    clean={k:v for k,v in item.items() if k not in ('why','editorial_note')}
    clean.update(PUBLIC_NOTE_REWRITES.get(clean.get('title'),{}))
    public_items.append(clean)
out={'version':5,'generated':'2026-08-17','scope':'Ranked animation watchlist covering anime, films, donghua and stylized animation worldwide.','items':public_items,'collections':COLLECTIONS,'franchises':FRANCHISES,'sources':SOURCES}
with open(ROOT / "public/catalog.json", "w", encoding="utf-8") as catalog_file:
    json.dump(out, catalog_file, ensure_ascii=False, indent=2)
    catalog_file.write("\n")
print('items',len(items),'collections',len(COLLECTIONS),'franchises',len(FRANCHISES))
print('first 20:',[x['title'] for x in items[:20]])
