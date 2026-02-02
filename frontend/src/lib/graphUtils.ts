import { Node, Edge } from "@xyflow/react";
import { ScanFileResponse } from "@/types";

export function fileToGraph(
  data: ScanFileResponse,
  fileName: string,
  spacing: number = 50
): { nodes: Node[], edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  let yOffset = 0;
  const X_START = 100;
  const Y_START = 50;

  // 1. File Node (Root)
  const fileNodeId = `file-${fileName}`;
  nodes.push({
    id: fileNodeId,
    type: 'input', // or special type if defined in MindMap
    data: { label: fileName, type: 'file' },
    position: { x: X_START + 300, y: Y_START },
    style: { fontWeight: 'bold', backgroundColor: '#f0f0f0', width: 200 }
  });

  yOffset += 150;

  // 2. Classes
  const classNodes: { [key: string]: Node } = {};

  if (data.classDetails && data.classDetails.length > 0) {
    data.classDetails.forEach((cls, i) => {
      const classId = `class-${cls.name}`;
      const classNode: Node = {
        id: classId,
        type: 'default',
        data: { label: `Class: ${cls.name}`, type: 'class' },
        position: { x: X_START + 300, y: Y_START + yOffset },
        style: { border: '2px solid #555', padding: '10px' }
      };
      nodes.push(classNode);
      classNodes[cls.name] = classNode;

      // Connect Class to File
      edges.push({
        id: `e-${fileNodeId}-${classId}`,
        source: fileNodeId,
        target: classId,
        animated: true
      });

      // Methods inside Class
      if (cls.methods && cls.methods.length > 0) {
        let methodY = 0;
        cls.methods.forEach((method, j) => {
          const methodId = `method-${cls.name}-${method.name}`;
          const methodLabel = method.name.includes('.') ? method.name.split('.').pop() : method.name;

          nodes.push({
            id: methodId,
            type: 'default',
            data: { label: `${methodLabel}()`, type: 'method' },
            position: { x: X_START + 600, y: Y_START + yOffset + methodY },
            parentId: undefined, // Could use parentId if we want them inside
            extent: undefined
          });

          // Connect Method to Class
          edges.push({
            id: `e-${classId}-${methodId}`,
            source: classId,
            target: methodId,
            type: 'smoothstep'
          });

          methodY += (spacing + 50);
        });

        // Adjust main yOffset based on methods height
        yOffset += Math.max(100, methodY);
      } else {
        yOffset += 100;
      }
    });
  }

  // 3. Standalone Functions
  // Reset Y for functions to distribute them
  let funcYOffset = 150;

  if (data.functions && data.functions.length > 0) {
    data.functions.forEach((funcName, i) => {
      const funcId = `func-${funcName}`;
      nodes.push({
        id: funcId,
        type: 'default',
        data: { label: `${funcName}()`, type: 'function' },
        position: { x: X_START, y: Y_START + funcYOffset },
      });

      // Connect Function to File
      edges.push({
        id: `e-${fileNodeId}-${funcId}`,
        source: fileNodeId,
        target: funcId,
        type: 'default',
        animated: true,
        style: { strokeDasharray: '5,5' }
      });

      funcYOffset += (spacing + 50);
    });
  }

  // 4. Dependencies (Internal Calls)
  if (data.dependencies) {
    Object.entries(data.dependencies).forEach(([caller, deps]) => {
      // Find caller node ID
      // Caller could be "funcName" or "ClassName.methodName" or just "methodName"?
      // Our IDs are `func-{name}`, `class-{name}`, `method-{cls}-{name}`.

      let callerId: string | undefined;

      // Try to match function
      if (nodes.find(n => n.id === `func-${caller}`)) {
        callerId = `func-${caller}`;
      } else {
        // Try to match method
        // Method names in dependencies might be simple "methodName" or "Class.methodName"
        // In our nodes we used `method-{cls}-{name}`.
        // We need to search nodes.
        const found = nodes.find(n => n.id.endsWith(`-${caller}`) || n.data.label === `${caller}()`);
        if (found) callerId = found.id;
      }

      if (callerId) {
        deps.calls.forEach(callee => {
          let calleeId: string | undefined;

          if (nodes.find(n => n.id === `func-${callee}`)) {
            calleeId = `func-${callee}`;
          } else {
            const found = nodes.find(n => n.id.endsWith(`-${callee}`) || n.data.label === `${callee}()`);
            if (found) calleeId = found.id;
          }

          if (calleeId && callerId !== calleeId) {
            edges.push({
              id: `dep-${callerId}-${calleeId}`,
              source: callerId,
              target: calleeId,
              type: 'default',
              animated: true,
              style: { stroke: '#ff0072' }
            });
          }
        });
      }
    });
  }

  return { nodes, edges };
}
