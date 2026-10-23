# Coding brief: cooperative acts in folklore motif descriptions (frozen 23 October 2026)

You will code short descriptions of folklore motifs, the recurring episodes and plot elements found in myths and tales. Code only what the description says. Do not use web search or outside knowledge of where a motif is told. Do not open any file except this brief, your batch file and your output file. Some names have been replaced by [NAME]; ignore that.

## What to code

For each motif, list every act in the description that is one of the seven behaviours below, or a violation of one. Characters can be people, animals, spirits or gods; treat them all as persons.

| behaviour | cooperative act (type = coop) | violation (type = violation) |
|---|---|---|
| family | helping, feeding, protecting, rescuing, avenging or caring for a relative (parent, child, sibling, spouse, in-law) | neglecting, abandoning, harming, killing or betraying a relative |
| group | helping, defending, sacrificing for, or bringing a benefit to one's own people, village or community | betraying, deserting or harming one's own people |
| reciprocity | returning a favour, repaying a debt, keeping a promise or bargain, showing gratitude, exchanging honestly | cheating, deceiving or tricking someone, breaking a promise or bargain, ingratitude, not repaying |
| bravery | courage: facing danger, fighting or enduring hardship | cowardice: fleeing, hiding, abandoning others out of fear |
| deference | obeying or respecting a parent, elder, chief, ruler or deity, including keeping a prohibition they set | disobeying, insulting or defying a parent, elder, chief, ruler or deity, including breaking a prohibition they set |
| fairness | dividing or sharing something equally, taking only one's share | taking more than one's share, unfair division, greedy hoarding of something that should be shared |
| property | respecting what belongs to others, returning lost or borrowed things | stealing, robbing, seizing what belongs to others |

## For each act, record

- behaviour: one of family, group, reciprocity, bravery, deference, fairness, property.
- type: coop or violation.
- target: who the act is directed at, from the actor's side. Use one of:
  - kin: a relative.
  - group: a member of the actor's own community, its chief or elders, or the people as a whole.
  - stranger: an unrelated person not described as hostile, such as a guest, host or traveller.
  - enemy: a hostile person or group, a rival, a monster, ogre, cannibal or hostile spirit.
  - deity: a god or spirit that is not hostile.
  - unclear.
- outcome: what happens to the actor as a result of this act, according to the description. Use one of:
  - rewarded: the actor succeeds, gains, is rewarded, praised, saved, marries well, or the act achieves its aim.
  - punished: the actor dies, suffers, is transformed as a penalty, is shamed, loses something, fails, or is condemned.
  - none: no outcome for the actor is stated or clearly implied.
- evidence: the words in the description that show the act and its outcome (at most 15 words, copied exactly).

## Rules

- Code an act only if the description states it or makes it unmistakable. Do not infer acts from the title alone, unless the title states one and the description is empty.
- One episode can contain several acts. Code each one. For example, a hero who steals fire from its hostile owner for the people involves two acts:
  - property, violation, target enemy;
  - group, coop, target group.
  If the description says the theft succeeds, both are rewarded.
- A trick or deception counts as a reciprocity violation, whoever the target is. If the trickster gains or escapes, the outcome is rewarded. If the trickster is exposed, fails or is punished, the outcome is punished.
- Many motifs describe the origin of things (the sun, animals, spots on the moon) with no act of these kinds. Record acts = [] for them. Most motifs will have no acts.
- If the outcome differs between versions ("usually", "in some versions"), code the outcome given as usual or first. If none is given as usual, use none.
- Be consistent. When unsure whether something is an act of one of these kinds, leave it out.

## Output

Write a JSON list, one object per motif in your batch and in the same order:

{"motif_id": "a1", "acts": [{"behaviour": "reciprocity", "type": "violation", "target": "stranger", "outcome": "punished", "evidence": "..."}]}

Use "acts": [] when there are none. Write only valid JSON to your output file. Your final reply gives:

- the number of motifs coded;
- the number with at least one act;
- any motif you could not code, and why.
