import javalang
import os
from collections import defaultdict
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate

# ----------- 1. Java Code Input (Paste your Java here) -----------
java_code = """
import java.util.*;

class Solution {
    public int carFleet(int t, int[] position, int[] speed) {
        int n = speed.length;
        float[] time = new float[n];
        HashMap<Integer,Integer> hm = new HashMap<>();
        for(int i=0; i<n; i++){
            hm.put(position[i],speed[i]);
        }
        Arrays.sort(position);
        Collections.reverse(Arrays.asList(position));
        Stack<Float> stk = new Stack<>();

        for(int i=0; i<n; i++){
            time[i] = (float)(t-position[i])/hm.get(position[i]);
        }

        for(int i=n-1; i>=0; i--){
            if(stk.isEmpty() || time[i] > stk.peek()){
                stk.push(time[i]);
            }
        }

        return stk.size();
    }
}
"""

# ----------- 2. Parse Java Code for Method Calls -----------
used_ds_types = set()
method_map_by_ds = defaultdict(set)              # HashMap → put(), get()
static_method_map_by_class = defaultdict(set)     # Arrays → sort(), etc.
var_to_type = {}

tree = javalang.parse.parse(java_code)

for path, node in tree:
    if isinstance(node, (javalang.tree.LocalVariableDeclaration, javalang.tree.FieldDeclaration)):
        if isinstance(node.type, javalang.tree.ReferenceType):
            base_type = node.type.name
            for declarator in node.declarators:
                var_to_type[declarator.name] = base_type
                used_ds_types.add(base_type)

for path, node in tree.filter(javalang.tree.MethodInvocation):
    if node.qualifier:
        if node.qualifier in var_to_type:
            ds_type = var_to_type[node.qualifier]
            method_map_by_ds[ds_type].add(node.member)
        elif node.qualifier[0].isupper():
            static_method_map_by_class[node.qualifier].add(node.member)

# ----------- 3. LangChain Setup for Gemini & FAISS VectorDB -----------
api_key = input("🔑 Enter your Google API Key: ").strip()
VECTOR_DB_DIR = "faiss_csv_index"

embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
db = FAISS.load_local(VECTOR_DB_DIR, embeddings, allow_dangerous_deserialization=True)

model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2, google_api_key=api_key)

prompt_template = """
Use the CSV context to explain the methods. If a method is not available in context, say so.

Context:
{context}

Question:
{question}

Answer:
"""
prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
qa_chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

# ----------- 4. Query Function for Explanation -----------
def explain_methods(library_name, methods):
    method_list = ', '.join(sorted(methods))
    question = f"Explain all the {method_list} methods"
    docs = db.similarity_search(question, k=10, filter={"library": library_name.lower()})

    if not docs:
        return f"\n📚 Library: {library_name}\n❌ No explanation found in the database."
    
    response = qa_chain({"input_documents": docs, "question": question}, return_only_outputs=True)
    return f"\n📚 Library: {library_name}\n{response['output_text'].strip()}"

# ----------- 5. Execute Queries and Print Results -----------
print("\n🔎 Grouped Method Explanations:\n")

# A. Instance Methods (from variables like hm, stk)
for ds_type, methods in sorted(method_map_by_ds.items()):
    print(explain_methods(ds_type, methods))

# B. Static Methods (like Arrays.sort, Collections.reverse)
for class_name, methods in sorted(static_method_map_by_class.items()):
    print(explain_methods(class_name, methods))
