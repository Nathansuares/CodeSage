import javalang
import os
from collections import defaultdict

# Main Java code
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

CSV_DIR = "./csv_files"

used_ds_types = set()
used_methods = set()
instantiations = []
var_to_type = {}  # variable name → data structure type
method_map_by_ds = defaultdict(set)  # object (e.g., hm) → method
static_method_map_by_class = defaultdict(set)  # Arrays, Collections, etc.

# Parse Java code
tree = javalang.parse.parse(java_code)

# 1. Variable declarations + instantiations
for path, node in tree:
    if isinstance(node, (javalang.tree.LocalVariableDeclaration, javalang.tree.FieldDeclaration)):
        var_type = node.type
        for declarator in node.declarators:
            instantiation = "N/A"
            if isinstance(var_type, javalang.tree.ReferenceType):
                base_type = var_type.name
                used_ds_types.add(base_type)
                var_to_type[declarator.name] = base_type

                init = declarator.initializer
                if isinstance(init, javalang.tree.ClassCreator):
                    try:
                        inst_type = init.type.name
                        inst_args = init.type.arguments
                        if inst_args:
                            gen = ', '.join([a.type.name for a in inst_args])
                            instantiation = f"{inst_type}<{gen}>"
                        else:
                            instantiation = f"{inst_type}<>"
                    except:
                        instantiation = init.type.name
                elif isinstance(init, javalang.tree.MethodInvocation):
                    if init.qualifier:
                        instantiation = f"{init.qualifier}.{init.member}(...)"
                    else:
                        instantiation = f"{init.member}(...)"

                instantiations.append((declarator.name, instantiation))

# 2. Method calls
for path, node in tree.filter(javalang.tree.MethodInvocation):
    used_methods.add(node.member)

    if node.qualifier:
        # Variable-based method call (e.g., hm.put)
        if node.qualifier in var_to_type:
            ds_type = var_to_type[node.qualifier]
            method_map_by_ds[ds_type].add(node.member)
        # Static class-based method call (e.g., Arrays.sort)
        elif node.qualifier[0].isupper():
            used_ds_types.add(node.qualifier)
            static_method_map_by_class[node.qualifier].add(node.member)

# ✅ Output

print("\n🔍 Data Structures Detected:")
for ds in sorted(used_ds_types):
    print(f" - {ds}")

print("\n🔨 Instantiations Detected:")
for var_name, instantiation in instantiations:
    print(f" - {var_name.ljust(4)}→  {f'new {instantiation}' if '<' in instantiation else instantiation}")

print("\n🔧 Instance Method Calls (Grouped by Object Type):")
for ds_type, methods in sorted(method_map_by_ds.items()):
    print(f" - {ds_type}: {', '.join(sorted(method + '()' for method in methods))}")

print("\n📌 Static Class Method Calls:")
for class_name, methods in sorted(static_method_map_by_class.items()):
    print(f" - {class_name}: {', '.join(sorted(method + '()' for method in methods))}")

print("\n📦 Matching CSV Files:")
for ds in sorted(used_ds_types):
    csv_filename = f"{ds}_methods.csv"
    csv_path = os.path.join(CSV_DIR, csv_filename)
    if os.path.isfile(csv_path):
        print(f"✅ CSV found for {ds}: {csv_filename}")
    else:
        print(f"❌ CSV NOT found for {ds}: {csv_filename}")
