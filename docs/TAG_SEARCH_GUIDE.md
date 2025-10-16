# 🔍 **Hammerspace Tag Search Guide**

## **Overview**

This guide provides comprehensive instructions for using the Volume Canvas MCP Server to search for files using tags. Tags are metadata labels that help organize and categorize your data for efficient management and tier operations.

---

## **📋 Table of Contents**

1. [Understanding Tags](#understanding-tags)
2. [Tag Search Tools](#tag-search-tools)
3. [Search Patterns and Examples](#search-patterns-and-examples)
4. [Advanced Search Techniques](#advanced-search-techniques)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## **1. Understanding Tags**

### **🏷️ What are Tags?**
Tags are key-value pairs that provide metadata about files and directories. They enable powerful search and organization capabilities.

### **📝 Tag Structure**
```json
{
  "name": "user.priority",
  "value": "high"
}
```

### **🔤 Tag Naming Conventions**
- **User Tags**: `user.*` (e.g., `user.project`, `user.priority`, `user.tier`)
- **System Tags**: `system.*` (e.g., `system.created`, `system.size`)
- **Custom Tags**: Any custom naming convention

### **📊 Common Tag Categories**
- **Project**: `user.project` (e.g., "ai-models", "data-analysis")
- **Priority**: `user.priority` (e.g., "high", "medium", "low")
- **Tier**: `user.tier` (e.g., "tier0", "tier1", "tier2")
- **Environment**: `user.env` (e.g., "production", "staging", "dev")
- **Data Type**: `user.type` (e.g., "model", "dataset", "backup")

---

## **2. Tag Search Tools**

### **🔍 Primary Search Tool: `search_files_by_tag`**

#### **Basic Syntax**
```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "string",
    "tag_value": "string (optional)",
    "path": "string (optional)"
  }
}
```

#### **Parameters**
- **`tag_name`** (required): The name of the tag to search for
- **`tag_value`** (optional): Specific value to match
- **`path`** (optional): Directory path to search within (default: "/")

#### **Response Format**
```json
{
  "tag_name": "user.priority",
  "tag_value": "high",
  "search_path": "/",
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
    }
  ],
  "total_count": 1,
  "timestamp": "2025-10-01T15:18:01.566Z"
}
```

### **📁 Secondary Tool: `list_files_with_tags`**

#### **Purpose**
List all files in a directory with their associated tags (useful for discovery).

#### **Syntax**
```json
{
  "tool": "list_files_with_tags",
  "arguments": {
    "path": "string (optional)",
    "limit": "integer (optional)"
  }
}
```

---

## **3. Search Patterns and Examples**

### **🎯 Exact Tag Name Search**
Find all files with a specific tag name, regardless of value.

```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.project"
  }
}
```

**Result**: Returns all files tagged with `user.project` (any value).

### **🎯 Exact Tag Value Search**
Find files with a specific tag name AND value.

```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.priority",
    "tag_value": "high"
  }
}
```

**Result**: Returns only files with `user.priority=high`.

### **🎯 Path-Scoped Search**
Search within a specific directory.

```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.tier",
    "tag_value": "tier0",
    "path": "/models"
  }
}
```

**Result**: Returns files in `/models` directory with `user.tier=tier0`.

### **🎯 Project-Based Search**
Find all files belonging to a specific project.

```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.project",
    "tag_value": "ai-models"
  }
}
```

### **🎯 Priority-Based Search**
Find high-priority files across the system.

```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.priority",
    "tag_value": "critical"
  }
}
```

### **🎯 Tier-Based Search**
Find files currently on a specific tier.

```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.tier",
    "tag_value": "tier0"
  }
}
```

### **🎯 Environment-Based Search**
Find files for a specific environment.

```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.env",
    "tag_value": "production"
  }
}
```

---

## **4. Advanced Search Techniques**

### **🔄 Multi-Step Search Strategy**

#### **Step 1: Discover Available Tags**
```json
{
  "tool": "list_files_with_tags",
  "arguments": {
    "path": "/",
    "limit": 10
  }
}
```

#### **Step 2: Refine Search Based on Discovery**
```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.project",
    "tag_value": "ai-models"
  }
}
```

### **🎯 Search for Untagged Files**
Use the list tool to find files without specific tags.

```json
{
  "tool": "list_files_with_tags",
  "arguments": {
    "path": "/models"
  }
}
```

Then manually filter results for files with empty `tags` arrays.

### **📊 Search Analytics**
Combine search results with system status for insights.

```json
{
  "tool": "get_system_status",
  "arguments": {}
}
```

---

## **5. Best Practices**

### **🏷️ Tagging Strategy**
1. **Consistent Naming**: Use consistent tag names across your organization
2. **Hierarchical Structure**: Use dot notation (e.g., `user.project.ai-models`)
3. **Standard Values**: Define standard values for common tags
4. **Documentation**: Document your tagging conventions

### **🔍 Search Strategy**
1. **Start Broad**: Begin with tag name searches to understand data
2. **Narrow Down**: Use specific values to refine results
3. **Path Scoping**: Use path parameters to limit search scope
4. **Regular Discovery**: Periodically use `list_files_with_tags` to discover new tags

### **📊 Performance Tips**
1. **Use Path Scoping**: Limit searches to relevant directories
2. **Batch Operations**: Process search results in batches
3. **Cache Results**: Store frequently used search results
4. **Monitor System**: Check system status before large searches

### **🔄 Workflow Integration**
1. **Tag First**: Tag files when they're created or modified
2. **Search Regularly**: Use searches to maintain data organization
3. **Automate**: Integrate tag searches into automated workflows
4. **Monitor**: Track search patterns to optimize tagging

---

## **6. Troubleshooting**

### **❌ Common Issues**

#### **Issue**: No results returned
**Possible Causes**:
- Tag name doesn't exist
- Tag value doesn't match exactly
- Path doesn't contain tagged files
- Case sensitivity issues

**Solutions**:
1. Use `list_files_with_tags` to discover available tags
2. Check tag names and values for typos
3. Verify path exists and contains files
4. Try broader searches first

#### **Issue**: Too many results
**Solutions**:
1. Add `tag_value` parameter to narrow results
2. Use `path` parameter to limit scope
3. Use more specific tag names

#### **Issue**: Search is slow
**Solutions**:
1. Use `path` parameter to limit search scope
2. Check system status for performance issues
3. Consider breaking large searches into smaller batches

### **🔧 Debugging Steps**

#### **Step 1: Verify System Status**
```json
{
  "tool": "get_system_status",
  "arguments": {}
}
```

#### **Step 2: Discover Available Tags**
```json
{
  "tool": "list_files_with_tags",
  "arguments": {
    "path": "/",
    "limit": 5
  }
}
```

#### **Step 3: Test Basic Search**
```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.project"
  }
}
```

#### **Step 4: Refine Search**
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

---

## **📖 Quick Reference**

### **🔍 Search Commands**
```bash
# Find all files with a tag
search_files_by_tag({"tag_name": "user.project"})

# Find files with specific tag value
search_files_by_tag({"tag_name": "user.priority", "tag_value": "high"})

# Search in specific directory
search_files_by_tag({"tag_name": "user.tier", "path": "/models"})

# List files with tags for discovery
list_files_with_tags({"path": "/", "limit": 10})
```

### **📊 Common Search Patterns**
- **Project Files**: `search_files_by_tag({"tag_name": "user.project", "tag_value": "project-name"})`
- **High Priority**: `search_files_by_tag({"tag_name": "user.priority", "tag_value": "high"})`
- **Tier 0 Files**: `search_files_by_tag({"tag_name": "user.tier", "tag_value": "tier0"})`
- **Production Data**: `search_files_by_tag({"tag_name": "user.env", "tag_value": "production"})`

---

## **🚀 Getting Started**

1. **Discover Tags**: Use `list_files_with_tags` to see what tags exist
2. **Basic Search**: Try `search_files_by_tag` with a known tag name
3. **Refine Results**: Add `tag_value` and `path` parameters
4. **Build Workflows**: Integrate searches into your data management processes

**🎯 Happy Tag Searching!** This guide should help you efficiently find and organize your data using the powerful tag search capabilities of the Volume Canvas MCP Server.
