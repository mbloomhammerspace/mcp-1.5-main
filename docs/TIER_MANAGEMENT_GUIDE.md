# 🎯 **Hammerspace Tier Management Guide**

## **Overview**

This guide demonstrates how to use the Volume Canvas MCP Server to manage data movement between storage tiers, specifically focusing on moving folders into **Tier 0** (the highest performance tier) and back out again.

---

## **📋 Table of Contents**

1. [Understanding Storage Tiers](#understanding-storage-tiers)
2. [Available MCP Tools](#available-mcp-tools)
3. [Step-by-Step Tier Management](#step-by-step-tier-management)
4. [Complete Workflow Examples](#complete-workflow-examples)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## **1. Understanding Storage Tiers**

### **🏆 Tier 0 (Hot Storage)**
- **Purpose**: Highest performance, fastest access
- **Use Cases**: Active data, frequently accessed files, real-time processing
- **Characteristics**: SSD-based, low latency, high IOPS
- **Cost**: Highest per GB

### **🌡️ Tier 1 (Warm Storage)**
- **Purpose**: Balanced performance and cost
- **Use Cases**: Regularly accessed data, staging areas
- **Characteristics**: Mixed SSD/HDD, moderate latency
- **Cost**: Medium per GB

### **❄️ Tier 2 (Cold Storage)**
- **Purpose**: Long-term storage, infrequent access
- **Use Cases**: Archives, backups, compliance data
- **Characteristics**: HDD-based, higher latency
- **Cost**: Lower per GB

### **🗄️ Archive Storage**
- **Purpose**: Long-term retention, compliance
- **Use Cases**: Legal holds, regulatory compliance
- **Characteristics**: Tape or object storage, very high latency
- **Cost**: Lowest per GB

---

## **2. Available MCP Tools**

### **🔍 Search and Discovery Tools**
- `search_files_by_tag` - Find files by tag criteria
- `list_files_with_tags` - List files with their associated tags
- `list_files` - List files in a directory

### **🏷️ Tagging Tools**
- `set_file_tag` - Add or update tags on files/directories

### **🎯 Objective Management Tools**
- `place_on_tier` - Create objectives to move data TO a specific tier
- `exclude_from_tier` - Create objectives to move data FROM a specific tier
- `apply_objective_to_files` - Apply objectives to multiple files at once

### **📊 Monitoring Tools**
- `list_jobs` - Monitor data movement jobs
- `get_system_status` - Check overall system health

---

## **3. Step-by-Step Tier Management**

### **🔄 Moving Data INTO Tier 0**

#### **Step 1: Identify Files to Move**
```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.priority",
    "tag_value": "high",
    "path": "/models"
  }
}
```

#### **Step 2: Apply Tier 0 Objective**
```json
{
  "tool": "place_on_tier",
  "arguments": {
    "path": "/models/high-priority",
    "tier_name": "tier0",
    "volume_type": "hot"
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

### **🔄 Moving Data OUT OF Tier 0**

#### **Step 1: Identify Files to Move**
```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.priority",
    "tag_value": "low",
    "path": "/models"
  }
}
```

#### **Step 2: Apply Exclusion Objective**
```json
{
  "tool": "exclude_from_tier",
  "arguments": {
    "path": "/models/low-priority",
    "tier_name": "tier0",
    "volume_type": "hot"
  }
}
```

#### **Step 3: Monitor Movement**
```json
{
  "tool": "list_jobs",
  "arguments": {
    "status_filter": "running"
  }
}
```

---

## **4. Complete Workflow Examples**

### **📁 Example 1: Move AI Model to Tier 0 for Training**

#### **Scenario**: You have a new AI model that needs to be moved to Tier 0 for high-performance training.

#### **Step 1: Tag the Model**
```json
{
  "tool": "set_file_tag",
  "arguments": {
    "file_path": "/models/new-model.pt",
    "tag_name": "user.priority",
    "tag_value": "critical"
  }
}
```

#### **Step 2: Search for Critical Models**
```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.priority",
    "tag_value": "critical"
  }
}
```

#### **Step 3: Move to Tier 0**
```json
{
  "tool": "place_on_tier",
  "arguments": {
    "path": "/models/new-model.pt",
    "tier_name": "tier0"
  }
}
```

#### **Step 4: Verify Movement**
```json
{
  "tool": "list_jobs",
  "arguments": {
    "status_filter": "running"
  }
}
```

### **📁 Example 2: Archive Old Data from Tier 0**

#### **Scenario**: You need to free up Tier 0 space by moving old, infrequently accessed data to cold storage.

#### **Step 1: Find Old Data**
```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.last_accessed",
    "tag_value": "2023-01-01"
  }
}
```

#### **Step 2: Tag for Archival**
```json
{
  "tool": "set_file_tag",
  "arguments": {
    "file_path": "/data/old-dataset.csv",
    "tag_name": "user.archive_candidate",
    "tag_value": "true"
  }
}
```

#### **Step 3: Exclude from Tier 0**
```json
{
  "tool": "exclude_from_tier",
  "arguments": {
    "path": "/data/old-dataset.csv",
    "tier_name": "tier0"
  }
}
```

#### **Step 4: Move to Cold Storage**
```json
{
  "tool": "place_on_tier",
  "arguments": {
    "path": "/data/old-dataset.csv",
    "tier_name": "tier2"
  }
}
```

### **📁 Example 3: Batch Operations on Multiple Files**

#### **Scenario**: You need to move multiple files based on a tag search.

#### **Step 1: Find All Files with Specific Tag**
```json
{
  "tool": "search_files_by_tag",
  "arguments": {
    "tag_name": "user.project",
    "tag_value": "ai-models"
  }
}
```

#### **Step 2: Apply Objective to All Files**
```json
{
  "tool": "apply_objective_to_files",
  "arguments": {
    "file_paths": [
      "/models/model1.pt",
      "/models/model2.pt",
      "/models/model3.pt"
    ],
    "objective_type": "place_on_tier",
    "tier_name": "tier0"
  }
}
```

---

## **5. Best Practices**

### **🏷️ Tagging Strategy**
- Use consistent tag naming conventions (e.g., `user.project`, `user.priority`)
- Tag files when they're created or modified
- Use tags to categorize data by access patterns
- Implement automated tagging based on file age, size, or type

### **🎯 Objective Management**
- Create objectives during low-usage periods
- Monitor job progress regularly
- Use batch operations for multiple files
- Test objectives on small datasets first

### **📊 Monitoring**
- Check system status before major operations
- Monitor job queues to avoid bottlenecks
- Set up alerts for failed jobs
- Keep track of tier utilization

### **🔄 Workflow Optimization**
- Plan tier movements in advance
- Use tags to automate tier management
- Implement lifecycle policies
- Regular cleanup of unused data

---

## **6. Troubleshooting**

### **❌ Common Issues**

#### **Issue**: Jobs stuck in "running" status
**Solution**: Check system resources and network connectivity
```json
{
  "tool": "get_system_status",
  "arguments": {}
}
```

#### **Issue**: Files not found in search
**Solution**: Verify tag names and values, check path permissions
```json
{
  "tool": "list_files_with_tags",
  "arguments": {
    "path": "/",
    "limit": 10
  }
}
```

#### **Issue**: Objectives not applying
**Solution**: Check tier availability and file permissions
```json
{
  "tool": "list_jobs",
  "arguments": {
    "status_filter": "failed"
  }
}
```

### **🔧 Debugging Steps**

1. **Check System Status**
   ```json
   {
     "tool": "get_system_status",
     "arguments": {}
   }
   ```

2. **Verify File Tags**
   ```json
   {
     "tool": "list_files_with_tags",
     "arguments": {
       "path": "/path/to/check"
     }
   }
   ```

3. **Monitor Active Jobs**
   ```json
   {
     "tool": "list_jobs",
     "arguments": {
       "status_filter": "all"
     }
   }
   ```

---

## **🚀 Quick Start Commands**

### **Move Folder to Tier 0**
```bash
# 1. Tag the folder
set_file_tag("/path/to/folder", "user.tier", "tier0")

# 2. Apply objective
place_on_tier("/path/to/folder", "tier0")

# 3. Monitor
list_jobs("running")
```

### **Move Folder from Tier 0**
```bash
# 1. Exclude from tier0
exclude_from_tier("/path/to/folder", "tier0")

# 2. Place on target tier
place_on_tier("/path/to/folder", "tier1")

# 3. Monitor
list_jobs("running")
```

---

## **📞 Support**

For additional help with tier management:
- Check the system logs for detailed error messages
- Verify your NVIDIA API key is properly configured
- Ensure you have appropriate permissions for the target paths
- Contact your Hammerspace administrator for tier configuration issues

---

**🎯 Happy Tier Managing!** This guide should help you efficiently move data between storage tiers using the Volume Canvas MCP Server with NVIDIA integration.
