import sqlite3
import google.generativeai as genai
from chromadb import Documents, EmbeddingFunction, Embeddings
import os
import re

def develop_context(subject):
  db = sqlite3.connect('super_stat_melee.db')
  cur = db.cursor()
  context = ''


  cur.execute(f"select exists(select 1 from tournaments where name like ? collate nocase)", (f"%{subject}%",))
  is_tournament = cur.fetchone()[0]
  if is_tournament:
    info = cur.execute('''select t.name, t.sortdate, t.city, t.liquipediatier, 
                                  t.winner_id, t.runnerup_id, t.winner_characters, 
                                  t.runnerup_characters, t.winner_country, t.runnerup_country
                          from tournaments as t
                          where name like ? collate nocase''', (f"%{subject}%",)).fetchall()
    for a in info:
        context += (f'tournament name: {a[0]}, sort date: {a[1]}, city: {a[2]}, '
                    f'liquipedia tier: {a[3]}, winner: {a[4]}, runner-up: {a[5]}, '
                    f'winner-character: {a[6]}, runner-up-character: {a[7]}, '
                    f'winner country: {a[8]}, runner-up country: {a[9]}\n')
    return context

  # Check if the subject is a player name
  cur.execute("select exists(select 1 from players where id like ? collate nocase)", (f"%{subject}%",))
  is_player = cur.fetchone()[0]
  if is_player:
    info = cur.execute('''select p.id, p.alternateid, p.name, p.nationality, p.birthdate, 
                          p.teampagename, p.earnings, p.status, p.mainmelee
                          from players as p
                          where id like ? collate nocase''', (f"%{subject}%",)).fetchall()
    for a in info:
        context += (f'player id: {a[0]}, alternate id: {a[1]}, name: {a[2]}, nationality: {a[3]}, '
                    f'birthdate: {a[4]}, team/sponser name: {a[5]}, earnings: {a[6]}, '
                    f'status: {a[7]}, main melee: {a[8]}\n')
    return context

  
  # info = cur.execute(f'''select t.name, t.winner_id, t.runnerup_id, t.winner_characters, t.runnerup_characters
  #                       from tournaments as t
  #                       where name == "{subject}" COLLATE NOCASE
  #   ''').fetchall()
  # context = ''
  # for a in info:
  #   context = 'tournament name: ' + a[0] + ' winner: ' + a[1] + ' runner-up: ' + a[2]
    #runner-up: {a[2]}, winner-character: {a[2]}, runner-up-character: {a[4]}'

  print(context)
  return context

def answer_question(question):
  
  gemini_api_key = os.getenv("GEMINI_API_KEY")
  if not gemini_api_key:
      raise ValueError("Gemini API Key not provided. Please provide GEMINI_API_KEY as an environment variable")
  genai.configure(api_key=gemini_api_key)
  model = genai.GenerativeModel('gemini-pro')
  match = re.search(r'["\']([^"\']*)["\']', question)
  entity = match.group(1) if match else None

  context = develop_context(entity)
  question = '''
      you are an chatbot specializing in Super Smash Melee tournaments. 
      The user will ask you a question, and you will respond in a full sentence with the answer derived from the context and only from the context.
      if the answer is not in the context given at the end of this prompt, say "i cannot answer that question". 
      here is the users question: ''' + question + "and here is the context: " + context + '''format your response 
      so that it is in plain text (remove all quotations) and gramtically correct with proper capitalization with a friendly tone'''
  response = model.generate_content(question)
  return response.text

if __name__ == "__main__":
  while True:
    question = input("Ask your question: ")
    if question.lower() == "exit":
      break
    answer = answer_question(question)
    print(answer)
