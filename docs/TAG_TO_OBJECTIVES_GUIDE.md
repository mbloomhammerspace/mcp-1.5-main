# 🎯 **Tag Search to Objectives Workflow Guide**

## **Overview**

This guide demonstrates how to use tag search results to apply objectives for tier management. This powerful workflow allows you to find files based on tags and then automatically apply tier objectives to those files.

---

## **📋 Table of Contents**

1. [Workflow Overview](#workflow-overview)
2. [Step-by-Step Process](#step-by-step-process)
3. [Complete Examples](#complete-examples)
4. [Advanced Workflows](#advanced-workflows)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## **1. Workflow Overview**

### **🔄 The Tag-to-Objectives Process**
1. **Search** for files using tags
2. **Extract** file paths from search results
3. **Apply** objectives to the found files
4. **Monitor** the objective execution

### **🎯 Available Objectives**
- **`place_on_tier`** - Move files TO a specific tier
- **`exclude_from_tier`** - Move files FROM a specific tier
- **`apply_objective_to_files`** - Apply objectives to multiple files

### **📊 Workflow Benefits**
- **Automated**: No manual file selection required
- **Scalable**: Handle hundreds of files at once
- **Flexible**: Use any tag criteria for file selection
- **Traceable**: Full audit trail of operations

---

## **2. Step-by-Step Process**

### **🔍 Step 1: Search for Files by Tags**

#### **Basic Tag Search**
```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.priority",
    "tag_value": "high"
  }
}
```

#### **Path-Scoped Search**
```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.project",
    "tag_value": "ai-models",
    "path": "/models"
  }
}
```

### **📋 Step 2: Extract File Paths**

From the search results, extract the `path` field from each file in `matching_files`:

```json
{
  "matching_files": [
    {
      "name": "model1.pt",
      "path": "/models/model1.pt",
      "size_mb": 500,
      "volume": "hot-storage",
      "matching_tag": {
        "name": "user.priority",
        "value": "high"
      }
    },
    {
      "name": "model2.pt", 
      "path": "/models/model2.pt",
      "size_mb": 750,
      "volume": "hot-storage",
      "matching_tag": {
        "name": "user.priority",
        "value": "high"
      }
    }
  ]
}
```

**Extracted paths**: `["/models/model1.pt", "/models/model2.pt"]`

### **🎯 Step 3: Apply Objectives to Files**

#### **Option A: Individual File Objectives**
```json
{
  "tool": "place_on_tier",
  "arguments": {
    "path": "/models/model1.pt",
    "tier_name": "tier0"
  }
}
```

#### **Option B: Batch File Objectives (Recommended)**
```json
{
  "tool": "apply_objective_to_files",
  "arguments": {
    "file_paths": [
      "/models/model1.pt",
      "/models/model2.pt"
    ],
    "objective_type": "place_on_tier",
    "tier_name": "tier0"
  }
}
```

### **📊 Step 4: Monitor Objective Execution**

```json
{
  "tool": "list_jobs",
  "arguments": {
    "status_filter": "running"
  }
}
```

---

## **3. Complete Examples**

### **📁 Example 1: Move High-Priority Files to Tier 0**

#### **Scenario**: Move all high-priority files to Tier 0 for maximum performance.

#### **Step 1: Search for High-Priority Files**
```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.priority",
    "tag_value": "high"
  }
}
```

#### **Step 2: Apply Tier 0 Objective**
```json
{
  "tool": "apply_objective_to_files",
  "arguments": {
    "file_paths": [
      "/models/model1.pt",
      "/models/model2.pt",
      "/data/dataset1.csv"
    ],
    "objective_type": "place_on_tier",
    "tier_name": "tier0"
  }
}
```

#### **Step 3: Monitor Progress**
```json
{
  "tool": "list_jobs",
  "arguments": {
    "status_filter": "running"
  }
}
```

### **📁 Example 2: Archive Old Project Files**

#### **Scenario**: Move all files from a completed project to cold storage.

#### **Step 1: Search for Project Files**
```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.project",
    "tag_value": "completed-project"
  }
}
```

#### **Step 2: Exclude from Tier 0**
```json
{
  "tool": "apply_objective_to_files",
  "arguments": {
    "file_paths": [
      "/projects/completed-project/file1.txt",
      "/projects/completed-project/file2.txt"
    ],
    "objective_type": "exclude_from_tier",
    "tier_name": "tier0"
  }
}
```

#### **Step 3: Place on Cold Storage**
```json
{
  "tool": "apply_objective_to_files",
  "arguments": {
    "file_paths": [
      "/projects/completed-project/file1.txt",
      "/projects/completed-project/file2.txt"
    ],
    "objective_type": "place_on_tier",
    "tier_name": "tier2"
  }
}
```

### **📁 Example 3: Environment-Based Tier Management**

#### **Scenario**: Move all development files to warm storage, production files to Tier 0.

#### **Step 1: Find Development Files**
```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.env",
    "tag_value": "development"
  }
}
```

#### **Step 2: Move Development Files to Warm Storage**
```json
{
  "tool": "apply_objective_to_files",
  "arguments": {
    "file_paths": [
      "/dev/model1.pt",
      "/dev/dataset1.csv"
    ],
    "objective_type": "place_on_tier",
    "tier_name": "tier1"
  }
}
```

#### **Step 3: Find Production Files**
```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.env",
    "tag_value": "production"
  }
}
```

#### **Step 4: Move Production Files to Tier 0**
```json
{
  "tool": "apply_objective_to_files",
  "arguments": {
    "file_paths": [
      "/prod/model1.pt",
      "/prod/dataset1.csv"
    ],
    "objective_type": "place_on_tier",
    "tier_name": "tier0"
  }
}
```

---

## **4. Advanced Workflows**

### **🔄 Multi-Criteria Search and Apply**

#### **Scenario**: Find files that meet multiple criteria and apply different objectives.

#### **Step 1: Search for High-Priority AI Models**
```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.priority",
    "tag_value": "high"
  }
}
```

#### **Step 2: Filter Results by File Type**
From the results, manually filter for files with `.pt` extension or use additional tag searches.

#### **Step 3: Apply Tier 0 Objective**
```json
{
  "tool": "apply_objective_to_files",
  "arguments": {
    "file_paths": [
      "/models/high-priority-model1.pt",
      "/models/high-priority-model2.pt"
    ],
    "objective_type": "place_on_tier",
    "tier_name": "tier0"
  }
}
```

### **📊 Conditional Workflow**

#### **Scenario**: Apply different objectives based on file characteristics.

#### **Step 1: Search for Large Files**
```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.size",
    "tag_value": "large"
  }
}
```

#### **Step 2: Check File Sizes and Apply Appropriate Objectives**
- Files > 1GB: Move to Tier 1
- Files < 1GB: Move to Tier 0

```json
{
  "tool": "apply_objective_to_files",
  "arguments": {
    "file_paths": ["/large/file1.pt"],
    "objective_type": "place_on_tier",
    "tier_name": "tier1"
  }
}
```

```json
{
  "tool": "apply_objective_to_files",
  "arguments": {
    "file_paths": ["/small/file2.pt"],
    "objective_type": "place_on_tier",
    "tier_name": "tier0"
  }
}
```

### **🔄 Automated Lifecycle Management**

#### **Scenario**: Implement automated data lifecycle based on age tags.

#### **Step 1: Find Old Files**
```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.age",
    "tag_value": "old"
  }
}
```

#### **Step 2: Archive Old Files**
```json
{
  "tool": "apply_objective_to_files",
  "arguments": {
    "file_paths": [
      "/old/file1.txt",
      "/old/file2.txt"
    ],
    "objective_type": "exclude_from_tier",
    "tier_name": "tier0"
  }
}
```

#### **Step 3: Move to Archive**
```json
{
  "tool": "apply_objective_to_files",
  "arguments": {
    "file_paths": [
      "/old/file1.txt",
      "/old/file2.txt"
    ],
    "objective_type": "place_on_tier",
    "tier_name": "archive"
  }
}
```

---

## **5. Best Practices**

### **🏷️ Tagging Strategy**
1. **Consistent Tagging**: Tag files when created or modified
2. **Hierarchical Tags**: Use structured tag names (e.g., `user.project.ai-models`)
3. **Standard Values**: Define standard values for common tags
4. **Lifecycle Tags**: Use tags to indicate data lifecycle stage

### **🔍 Search Strategy**
1. **Start Specific**: Use specific tag values to get precise results
2. **Validate Results**: Review search results before applying objectives
3. **Batch Operations**: Use `apply_objective_to_files` for multiple files
4. **Path Scoping**: Use path parameters to limit search scope

### **🎯 Objective Strategy**
1. **Test First**: Apply objectives to small test sets first
2. **Monitor Progress**: Track job execution and completion
3. **Error Handling**: Check for failed jobs and retry if needed
4. **Documentation**: Keep records of applied objectives

### **📊 Workflow Optimization**
1. **Automate**: Create scripts for common tag-to-objective workflows
2. **Schedule**: Run workflows during low-usage periods
3. **Monitor**: Set up alerts for failed objectives
4. **Review**: Regularly review and optimize workflows

---

## **6. Troubleshooting**

### **❌ Common Issues**

#### **Issue**: No files found in search
**Solutions**:
1. Verify tag names and values exist
2. Check path parameter is correct
3. Use `list_files_with_tags` to discover available tags
4. Try broader searches first

#### **Issue**: Objectives not applying
**Solutions**:
1. Check file paths are correct
2. Verify tier names are valid
3. Check system status for issues
4. Monitor job status for errors

#### **Issue**: Jobs stuck in running state
**Solutions**:
1. Check system resources
2. Verify network connectivity
3. Check for conflicting objectives
4. Restart stuck jobs if necessary

### **🔧 Debugging Workflow**

#### **Step 1: Verify System Status**
```json
{
  "tool": "get_system_status",
  "arguments": {}
}
```

#### **Step 2: Test Tag Search**
```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.project"
  }
}
```

#### **Step 3: Test Single File Objective**
```json
{
  "tool": "place_on_tier",
  "arguments": {
    "path": "/test/file.txt",
    "tier_name": "tier0"
  }
}
```

#### **Step 4: Test Batch Objective**
```json
{
  "tool": "apply_objective_to_files",
  "arguments": {
    "file_paths": ["/test/file.txt"],
    "objective_type": "place_on_tier",
    "tier_name": "tier0"
  }
}
```

---

## **📖 Quick Reference**

### **🔄 Complete Workflow Template**
```bash
# 1. Search for files
search_files_by_tag({"tag_name": "user.priority", "tag_value": "high"})

# 2. Extract file paths from results
# file_paths = ["/path1", "/path2", "/path3"]

# 3. Apply objective to files
apply_objective_to_files({
  "file_paths": file_paths,
  "objective_type": "place_on_tier",
  "tier_name": "tier0"
})

# 4. Monitor progress
list_jobs({"status_filter": "running"})
```

### **🎯 Common Workflow Patterns**
- **High Priority → Tier 0**: `search_files_by_tag({"tag_name": "user.priority", "tag_value": "high"})` → `place_on_tier("tier0")`
- **Old Files → Archive**: `search_files_by_tag({"tag_name": "user.age", "tag_value": "old"})` → `exclude_from_tier("tier0")` → `place_on_tier("archive")`
- **Project Files → Warm**: `search_files_by_tag({"tag_name": "user.project", "tag_value": "project-name"})` → `place_on_tier("tier1")`

---

## **🚀 Getting Started**

1. **Tag Your Files**: Ensure files have appropriate tags
2. **Test Search**: Use `search_files_by_tag` to find files
3. **Apply Objectives**: Use `apply_objective_to_files` for batch operations
4. **Monitor Results**: Use `list_jobs` to track progress
5. **Build Workflows**: Create automated processes for common operations

**🎯 Happy Tag-to-Objectives Workflow Management!** This guide should help you efficiently use tag searches to apply tier objectives for optimal data management.
