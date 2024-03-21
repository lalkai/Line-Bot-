from pythainlp.tokenize import word_tokenize
from sklearn.metrics.pairwise import cosine_similarity
from pythainlp import word_vector
from pythainlp.ulmfit import replace_rep_nonum
import random
import numpy as np
import json
from simpletransformers.t5 import T5Model
import torch



model = word_vector.WordVector(model_name="ltw2v").get_model() 

with open("qa_cp.json", encoding="utf8") as json_file:
  qa_data = json.load(json_file)

def thai2fit_sentence_vec(text):

  dim = 400
  vec = np.zeros((1,dim))
  for w in text:
    if w in model.index_to_key:
      vec += model.get_vector(w)
    else:
      continue
  return vec

def ask_2(qa):
  q = replace_rep_nonum(qa)
  q = word_tokenize(q, engine="newmm")
  lenQ = len(q)

  maxCosine = 0
  kp = ""

  q = thai2fit_sentence_vec(q)
  for Key in qa_data.keys():
    Key =  replace_rep_nonum(Key)
    k = word_tokenize(Key, engine="newmm")
    
    
    cossim = cosine_similarity(q,thai2fit_sentence_vec(k))[0][0]

    if cossim > maxCosine:
      kp = Key
      maxCosine = cossim
      
  if maxCosine > 0.7:
   
    return(random.choice(qa_data[kp]))
  elif lenQ < 10:
    return "ไม่สามารถสรุปให้ได้"
  else:
    
    cuda =  torch.cuda.is_available()

    pred_params = {
        'max_seq_length': 128,
        'use_multiprocessed_decoding': False
        }

    model = T5Model('mt5', 'best_model', args=pred_params, use_cuda=cuda) 
    pred = model.predict(list([str(qa)]))
  
    return(str(pred).replace("[","").replace("]","").replace("'",""))
