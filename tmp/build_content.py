import json
from pathlib import Path
rows=json.loads(Path('tmp/source-reference.json').read_text())
explanations=[
['Bruised skin does not answer the evidence about the blade. The gadget attacks Tomato instead of his argument. That is a Personal Attack.', 'Being a fruit or a vegetable does not tell us whether Tomato saw the spill. The gadget attacks him instead of the evidence. That is a Personal Attack.'],
['Many utensils believing Tomato stole the salt is not evidence that he did. Popular beliefs can be wrong. That is Bandwagon.', 'The gadgets agreeing about witnesses does not make them more reliable. Popularity is used in place of evidence. That is Bandwagon.'],
['A cracked handle and a difficult week do not show who shredded the recipe. The gadget asks for sympathy instead of giving evidence. That is Appeal to Pity.', 'Being sent to the junk drawer sounds sad, but it does not show who ruined the soup. Sympathy replaces evidence. That is Appeal to Pity.'],
['Knowing how to make ice does not make someone an expert on theft. The gadget relies on an unrelated expert. That is Irrelevant Authority.', 'Winning cake contests does not prove skill at identifying scratches. The gadget uses the wrong kind of expertise. That is Irrelevant Authority.'],
['The Chef can reject this accusation and still say spills are wrong. The gadget hides other possible choices. That is a False Dilemma.', 'Other residents had access too. The gadget pretends only two suspects are possible. That is a False Dilemma.'],
['One tomato falling does not prove all tomatoes lack control, or that this one hit the cake. The claim goes beyond the evidence. That is Hasty Generalization.', 'One wrong breakfast detail does not make every statement false. A tiny sample is used to judge everything. That is Hasty Generalization.'],
['Tomato asked for a protective cover, not for every gadget to be locked away. The peeler attacks a changed version of the idea. That is a Straw Man.', 'Tomato questions one clue, not all physical evidence. Toaster changes his claim into an easier one to attack. That is a Straw Man.'],
['The dirty oven does not explain frosting on the whisk. A different issue distracts from the original question. That is a Red Herring.', 'Seeds on the board do not explain whether the cord spilled milk. Changing topics avoids the question. That is a Red Herring.'],
['Tomato dripping juice does not answer whether the gadget dripped grease. Pointing to similar wrongdoing avoids the criticism. That is Whataboutism.', 'Tomato blocking a drain before does not explain who blocked it now. The gadget points back at its accuser. That is Whataboutism.'],
['The grater calls its story accurate because it is reliable, then calls itself reliable because of the same story. Nothing new supports it. That is Circular Reasoning.', 'Calling Tomato a thief just repeats the claim that he stole basil. A claim cannot prove itself. That is Circular Reasoning.'],
['Not proving he stayed away does not prove Tomato entered the pantry. A missing disproof is treated as proof. That is Appeal to Ignorance.', 'Lack of proof that the blades made scratches does not prove they did not. Missing evidence is not proof of the opposite. That is Appeal to Ignorance.'],
['The soup curdling after Tomato arrived does not prove he caused it. Happening afterward is not enough to show a cause. That is False Cause.', 'The lights failing after an accusation does not show the words caused it. The order of events is treated as proof. That is False Cause.'],
['Keeping one leaf does not prove Tomato will empty the pantry. The gadget predicts bigger and bigger problems without support. That is a Slippery Slope.', 'Questioning one witness does not prove dinner will never be served. The gadget jumps to an extreme outcome. That is a Slippery Slope.'],
['An empty can and a living tomato differ in ways that matter. Throwing away one does not justify throwing away the other. That is a False Analogy.', 'A noisy blender and a defendant objecting have different roles. Unplugging one does not justify silencing the other. That is a False Analogy.'],
['Sharp means clever for a witness, but it means able to cut for blades. The gadget switches meanings to make its claim. That is Equivocation.', 'Ripe for an argument is a figure of speech, not an admission of starting a fight. The meaning changes in the argument. That is Equivocation.'],
['The question assumes Tomato stole the spoon before that has been proved. Answering where would accept that hidden claim. That is a Loaded Question.', 'Yes or no would accept that Tomato used to sneak into the fridge. That has not been proved. That is a Loaded Question.'],
['The gadget shows one frame and hides the next frame with important evidence about its cord. Choosing only helpful evidence is Cherry-Picking.', 'The full conversation shows Tomato reading a recipe. Leaving that out changes what the words seem to mean. That is Cherry-Picking.'],
['Tomato supplies the requested photo, then the gadget demands a video. It changes the rule after the original demand is met. That is Moving the Goalposts.', 'The gadget asks for one witness, gets one, then demands three and excludes appliances. It changes the standard after it is met. That is Moving the Goalposts.'],
]
old=json.loads(Path('data/questions.json').read_text())['questions']
fallacies=[];questions=[]
for i,row in enumerate(rows):
    examples=[x.strip('"').replace('—',' - ') for x in row['examples']]
    fallacies.append(dict(id=row['id'],name=row['name'],definition=row['definition'],example=examples[0]))
    for j,argument in enumerate(examples):
        questions.append(dict(id=f'ref_{i+1:02}_{j+1}',fallacy=row['id'],argument=argument,explanation=explanations[i][j],source='Project plan Section 6.1; explanation adapted for gameplay'))
legacy=json.loads(Path('tmp/source-drafts.json').read_text())
for row in legacy:
    fallacy=next(f for f in fallacies if f['id']==row['fallacy'])
    row['explanation']=("The speaker attacks a person's traits instead of checking the evidence. Those traits do not prove the claim wrong. That is a Personal Attack." if row['fallacy']=='ad_hominem' else "What many people like or believe does not prove what is right or true. The speaker uses popularity as proof. That is Bandwagon." if row['fallacy']=='bandwagon' else "The speaker presents only two choices, but other choices are possible. Leaving those out is a False Dilemma.")
    row['source']='Project plan Section 6.5 draft; requires content review'
    questions.append(row)
for q in old:
    q['id']='prototype_'+q['id']
    q['source']='Preserved prototype draft; requires content review'
questions.extend(old)
for q in questions:
    assert len(q['argument'])<=220,(q['id'],len(q['argument']))
    assert len(q['explanation'])<=260,(q['id'],len(q['explanation']))
Path('data/fallacies.json').write_text(json.dumps({'fallacies':fallacies},indent=2,ensure_ascii=False)+'\n')
Path('data/questions.json').write_text(json.dumps({'questions':questions},indent=2,ensure_ascii=False)+'\n')
print(len(fallacies),'fallacies;',len(questions),'questions')
