#!/usr/bin/env python3
"""
Generic Database vs. Code Enum Consistency Validator
Enforces that database values match code Enum definitions, preventing silent validation crashes.
"""
import os
import sys
import argparse
from enum import Enum

# Standard color output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

# Example enum to demonstrate validation
class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

def get_real_db_values(collection_name):
    """
    Mock database extraction.
    In real projects, integrate your database connection here:
    
    Example for MongoDB (motor):
        client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
        db = client["your_database"]
        real_values = await db[collection_name].distinct("status")
        
    Example for PostgreSQL (SQLAlchemy):
        result = db.execute(text("SELECT DISTINCT status FROM orders"))
        real_values = [row[0] for row in result]
    """
    # Demonstration mock values representing what is in the DB
    mock_db = {
        "orders": ["pending", "processing", "completed", "cancelled"]
    }
    return mock_db.get(collection_name, [])

def validate_enum_consistency(enum_class, db_values, name="Enum"):
    """
    Performs symmetric set difference check between the code enum and real DB values.
    """
    print(f"🔍 Validating {BLUE}{name}{NC} consistency vs Database...")
    
    enum_values = [item.value for item in enum_class]
    
    print(f"   📊 Values in DB: {db_values}")
    print(f"   📊 Values in Code: {enum_values}")
    
    missing_in_code = set(db_values) - set(enum_values)
    missing_in_db = set(enum_values) - set(db_values)
    
    success = True
    
    if missing_in_code:
        print(f"   {RED}❌ DISCREPANCY: Found database values missing in code Enum!{NC}")
        for value in missing_in_code:
            print(f"      - Value '{value}' exists in DB but is not defined in OrderStatus")
        print(f"   💡 Action: Add {value.upper()} = \"{value}\" to your OrderStatus Enum.")
        success = False
        
    if missing_in_db:
        print(f"   {YELLOW}⚠️  Warning: Defined Enum values not present in DB (possibly unused):{NC}")
        for value in missing_in_db:
            print(f"      - Value '{value}' is in Code but not in DB")
            
    if success:
        print(f"   {GREEN}✅ {name} validation SUCCESSFUL!{NC}\n")
    else:
        print(f"   {RED}❌ {name} validation FAILED!{NC}\n")
        
    return success

def main():
    parser = argparse.ArgumentParser(description="Validate Code Enums vs Database Values")
    parser.add_argument("--db-url", help="Database connection URL")
    args = parser.parse_args()
    
    print(f"{BLUE}======================================================================{NC}")
    print(f"⚡ IA-Framework Enum Integrity Checker ⚡")
    print(f"{BLUE}======================================================================{NC}\n")
    
    # 1. Fetch values
    db_values = get_real_db_values("orders")
    
    # 2. Validate
    success = validate_enum_consistency(OrderStatus, db_values, "OrderStatus")
    
    if success:
        print(f"{GREEN}✅ All critical enums are fully consistent!{NC}")
        return 0
    else:
        print(f"{RED}❌ Enum validation failures detected! Correct before proceeding.{NC}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
