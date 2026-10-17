# AWS DynamoDB and RDS

**Name:** Srinidhi Narendran · **Roll No:** 24BCS10037

My notes comparing the two main AWS database services. I wanted to understand which one fits GearLoan, the equipment lending app I am building on EKS in `ap-south-1`.

---

# Part 1: DynamoDB

## NoSQL

DynamoDB is a fully managed **NoSQL key-value and document** database.

- No servers to manage, no patching, no fixed schema.
- Fast and steady response time (single-digit milliseconds) at almost any scale.
- Data is copied across 3 AZs in the region automatically.
- No SQL joins. I design the table around how the app will **read** the data.
- I can query it with the API or with PartiQL (a SQL-like syntax).

Capacity modes:

| Mode | How billing works | Good for |
|---|---|---|
| On-demand | Pay per read/write request | New apps, unknown traffic (what I will use) |
| Provisioned | Set read/write capacity units, can auto scale | Steady, predictable traffic |

## Tables

A table is a collection of items. When I create it, I only define the **primary key**. Other attributes can be different on each item.

```bash
aws dynamodb create-table \
  --table-name GearLoanLoans \
  --attribute-definitions AttributeName=item_id,AttributeType=S AttributeName=loan_date,AttributeType=S \
  --key-schema AttributeName=item_id,KeyType=HASH AttributeName=loan_date,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region ap-south-1
```

Extra table features I noted:
- **Global Secondary Index (GSI)**: query by a different key (e.g. by `student_id`).
- **TTL**: auto-delete items after a timestamp.
- **Streams**: send every change to Lambda or other consumers.
- **Point-in-time recovery**: restore the table to any second in the recovery window.

## Items

An item is one record, like a row. Maximum item size is **400 KB**.

A small item from GearLoan (one loan of one camera):

```json
{
  "item_id":    "CAM-1042",
  "loan_date":  "2026-10-14T10:30:00Z",
  "item_name":  "Canon EOS 200D",
  "student_id": "24BCS10037",
  "status":     "BORROWED",
  "due_date":   "2026-10-21",
  "accessories": ["battery", "18-55mm lens"]
}
```

## Attributes

An attribute is one field of an item (like a column, but not every item needs it).

| Type | Code | Example |
|---|---|---|
| String | S | `"CAM-1042"` |
| Number | N | `3` |
| Boolean | BOOL | `true` |
| Binary | B | image bytes (better kept in S3) |
| List | L | `["battery", "lens"]` |
| Map | M | `{"city": "Mumbai"}` |
| String set | SS | `["red", "blue"]` |
| Null | NULL | `null` |

## Partition key

The **partition key** (HASH key) decides which internal partition stores the item.

- If the table has only a partition key, it must be unique per item.
- Pick a key with many different values so load spreads evenly. A bad key (like `status`) creates "hot" partitions.
- In GearLoan, `item_id` is the partition key.

## Sort key

The **sort key** (RANGE key) is optional. Partition key + sort key together form a **composite primary key**.

- Many items can share a partition key if their sort keys differ.
- Items with the same partition key are stored sorted by the sort key.
- Lets me run range queries like `begins_with`, `between`, `>`.

Example: get all loans of one camera in 2026.

```bash
aws dynamodb query --table-name GearLoanLoans \
  --key-condition-expression "item_id = :id AND begins_with(loan_date, :y)" \
  --expression-attribute-values '{":id":{"S":"CAM-1042"},":y":{"S":"2026"}}'
```

## DynamoDB use cases

- Session data, user carts, shopping lists
- Leaderboards and counters for games
- IoT and event data with high write rates
- Serverless apps with Lambda and API Gateway
- Lookup by known key, like "loan history of item X"
- Terraform state locking (older setups; newer Terraform can lock with S3 directly)

---

# Part 2: RDS

## Relational database

RDS (Relational Database Service) runs SQL databases for me. AWS handles setup, patching, backups and failover. I still design the schema and write the SQL.

- Data is stored in tables with fixed columns and relationships (foreign keys).
- Supports joins and ACID transactions.
- I do not get OS access (except RDS Custom for Oracle and SQL Server).

## Supported engines

| Engine | Notes |
|---|---|
| Amazon Aurora (MySQL-compatible) | AWS built, storage copied 6 ways across 3 AZs |
| Amazon Aurora (PostgreSQL-compatible) | Same as above, PostgreSQL flavor |
| MySQL | Open source |
| PostgreSQL | Open source, what I would pick for GearLoan |
| MariaDB | Open source, MySQL fork |
| Oracle | Commercial, license included or bring your own |
| Microsoft SQL Server | Commercial |
| IBM Db2 | Commercial |

## DB instances

A DB instance is one database server in RDS. I choose:

- Instance class, e.g. `db.t4g.micro` (burstable), `db.m7g.large`, `db.r7g.large` (memory)
- Storage type: gp3 (general SSD) or io2 (provisioned IOPS). Storage autoscaling can grow it.
- Engine version, VPC, **DB subnet group** (subnets in at least 2 AZs), security group.

```bash
aws rds describe-db-instances --region ap-south-1 \
  --query "DBInstances[].[DBInstanceIdentifier,Engine,DBInstanceStatus]" --output table
```

## Security

- Run RDS in **private subnets** and set "publicly accessible" to No.
- Use a **security group** that only allows the DB port from the app (e.g. 5432 from the EKS node SG).
- **Encryption at rest** with KMS. It must be chosen at creation time.
- **Encryption in transit** with SSL/TLS; can be forced with a parameter (e.g. `rds.force_ssl` for PostgreSQL).
- Keep the master password in **AWS Secrets Manager** (RDS can manage and rotate it).
- **IAM database authentication** for MySQL and PostgreSQL, so apps can log in with a token instead of a password.

## Backups

| Type | Details |
|---|---|
| Automated backups | Daily snapshot + transaction logs. Retention 1 to 35 days. Allows point-in-time restore |
| Manual snapshots | I take them myself. Kept until I delete them |
| AWS Backup | Central backup plans across services |

- Restoring always creates a **new** DB instance. It does not overwrite the old one.
- Snapshots can be copied to another region for disaster recovery.

## Multi-AZ

Multi-AZ is for **high availability**, not for scaling reads.

- **Multi-AZ DB instance**: one primary and one standby in another AZ. Data is copied synchronously. The standby cannot serve reads.
- **Multi-AZ DB cluster** (MySQL and PostgreSQL): one writer and two readable standbys in three AZs.
- If the primary fails, RDS fails over automatically and the DNS endpoint points to the new primary. My app keeps the same endpoint.

## Read replicas

Read replicas are for **scaling reads**.

- Data is copied **asynchronously**, so a replica can lag a little.
- Each replica has its own endpoint. The app must send read queries there.
- Up to 15 read replicas for MySQL, MariaDB and PostgreSQL.
- Can be in another region (cross-region replica).
- A replica can be **promoted** to a standalone database.

| | Multi-AZ | Read replica |
|---|---|---|
| Main goal | Availability | Read performance |
| Replication | Synchronous | Asynchronous |
| Readable | Only in Multi-AZ DB cluster | Yes |
| Failover | Automatic | Manual promote |

## RDS use cases

- Web apps with users, orders, bookings (relational data)
- Apps that need joins, transactions and constraints
- Moving an existing MySQL or PostgreSQL app to the cloud
- Reporting with read replicas

---

## Which one for GearLoan?

| Need | Better fit |
|---|---|
| Students, items, loans with relations and reports | RDS PostgreSQL |
| Simple "loan history per item" at high speed, no server to size | DynamoDB |

My plan: start with DynamoDB on-demand for the loans table because it has no idle cost and needs no subnet or instance setup. If the app needs joins and reports later, I will move to RDS PostgreSQL in private subnets.
