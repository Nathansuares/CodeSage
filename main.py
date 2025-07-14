import javalang
import os

java_code = """
import java.util.*;

class Solution {
    HashMap<Character, Integer> globalMap = new HashMap<>();

    public List<Integer> partitionLabels(String s) {
        HashMap<Character,Integer> hm = new HashMap<>();
        int n = s.length();
        for(int i=0; i<n; i++){
            hm.put(s.charAt(i),i);
        }

        List<Integer> res = new ArrayList<>();
        int end = 0;
        int size = 0;

        for(int i=0; i<n; i++){
            size += 1;
            end = Math.max(end,hm.get(s.charAt(i)));

            if(end == i){
                res.add(size);
                size = 0;
            }
        }

        return res;
    }
}
"""

# Directory where CSV files are located
CSV_DIR = "./csv_files"

# Track data structures and methods
used_ds_types = set()
used_methods = set()

# Parse Java
tree = javalang.parse.parse(java_code)

# Traverse all nodes
for path, node in tree:
    # Handle local + field variable declarations
    if isinstance(node, (javalang.tree.LocalVariableDeclaration, javalang.tree.FieldDeclaration)):
        var_type = node.type
        for declarator in node.declarators:
            if isinstance(var_type, javalang.tree.ReferenceType):
                base_type = var_type.name
                used_ds_types.add(base_type)

# Traverse method invocations
for path, node in tree.filter(javalang.tree.MethodInvocation):
    used_methods.add(node.member)

# Print detected DS and methods
print("🔍 Data Structures Detected:")
for ds in used_ds_types:
    print(f" - {ds}")

print("\n🔧 Method Calls Detected:")
for method in used_methods:
    print(f" - {method}()")

# Check for CSV existence
print("\n📦 Matching CSV Files:")
for ds in used_ds_types:
    csv_filename = f"{ds}_methods.csv"  # updated naming convention
    csv_path = os.path.join(CSV_DIR, csv_filename)
    if os.path.isfile(csv_path):
        print(f"✅ CSV found for {ds}: {csv_filename}")
    else:
        print(f"❌ CSV NOT found for {ds}: {csv_filename}")
