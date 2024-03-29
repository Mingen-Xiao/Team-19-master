import enum
from sql_metadata import Parser
import sqlparse
from collections import deque
from sqlparse.sql import TokenList
from mo_sql_parsing import parse
import xlwt


sqlquery =           """
       SELECT main_qry.*,
       subdays.DAYS_OFFER1,
       subdays.DAYS_OFFER2,
       subdays.DAYS_OFFER3
from (
         SELECT jr.id  as PROJECT_ID,
                5 * (DATEDIFF(ifnull(lc.creation_date, now()), jr.creation_date) DIV 7)
                    + MID('0123444401233334012222340111123400001234000123440',
                          7 * WEEKDAY(jr.creation_date)
                          + WEEKDAY(ifnull(lc.creation_date, now())) + 1, 1)
                          as LIFETIME,
                count(distinct
                      case when jra.application_source = 'VERAMA'
                        then jra.id else null end)        NUM_APPLICATIONS,
                count(distinct jra.id) NUM_CANDIDATES,
                sum(case when jro.stage = 'DEAL' then 1 else 0 end) as NUM_CONTRACTED,
                sum(ifnull(IS_INTERVIEW, 0)) as NUM_INTERVIEWED,
                sum(ifnull(IS_PRESENTATION, 0)) as NUM_OFFERED
         from job_request jr
                  left join job_request_application jra on jr.id = jra.job_request_id
                  left join job_request_offer jro
                  on jro.job_request_application_id = jra.id
                  left join lifecycle lc on lc.object_id=jr.id
                  and lc.lifecycle_object_type='JOB_REQUEST'
                  and lc.event = 'JOB_REQUEST_CLOSED'
                  left join (SELECT jro2.job_request_application_id,
                                    max(case
                                            when jro2.first_interview_scheduled_date
                                            is not null then 1
                                            else 0 end) as IS_INTERVIEW,
                                    max(case when jro2.first_presented_date is not null
                                    then 1 else 0 end) as IS_PRESENTATION
                             from job_request_offer jro2
                             group by 1) jrah2
                             on jra.id = jrah2.job_request_application_id
                  left join client u on jr.client_id = u.id
         where jr.from_point_break = 0
           and u.name not in ('Test', 'Demo Client')
         group by 1, 2) main_qry
         left join (
    SELECT PROJECT_ID,
           sum(case when RowNo = 1 then days_to_offer else null end) as DAYS_OFFER1,
           sum(case when RowNo = 2 then days_to_offer else null end) as DAYS_OFFER2,
           sum(case when RowNo = 3 then days_to_offer else null end) as DAYS_OFFER3
    from (SELECT PROJECT_ID,
                 days_to_offer,
                 (SELECT count(distinct jro.job_request_application_id)
                  from job_request_offer jro
                           left join job_request_application jra2
                           on jro.job_request_application_id = jra2.id
                  where jra2.job_request_id = PROJECT_ID
                    and jro.first_presented_date is not null
                    and jro.first_presented_date <= InitialChangeDate
                 ) as RowNo
          from (
                   SELECT jr.id                    as PROJECT_ID,
                          5 * (
                          DATEDIFF(jro.first_presented_date, jr.creation_date) DIV 7) +
                          MID('0123444401233334012222340111123400001234000123440',
                              7 * WEEKDAY(jr.creation_date)
                              + WEEKDAY(jro.first_presented_date) + 1,
                              1)                   as days_to_offer,
                          jro.job_request_application_id,
                          jro.first_presented_date as InitialChangeDate
                   from presentation pr
                            left join presentation_job_request_offer pjro
                            on pr.id = pjro.presentation_id
                            left join job_request_offer jro
                            on pjro.job_request_offer_id = jro.id
                            left join job_request jr on pr.job_request_id = jr.id
                   where jro.first_presented_date is not null) days_sqry) days_final_qry
    group by PROJECT_ID) subdays
                   on subdays.PROJECT_ID = main_qry.PROJECT_ID

        """
sqlquery2 =                  """
SELECT '%c%' AS Chapter, 
    CASE
           WHEN ticket.status IN ('new', 'assigned')
                AND ticket_custom.ticket = 3 THEN 'Win'
           WHEN ticket.status IN ('new',
                                  'assigned')
                AND ticket_custom.ticket = 2 THEN 'Lose'
           WHEN ticket.status IN ('new',
                                  'assigned')
                AND ticket_custom.ticket = 1 THEN 'Draw'
           WHEN ticket.status IN ('new',
                                  'assigned')
                AND EmployeeConsolidated.id= 49887 THEN 'Undefined'
       END AS Feature,
       ticket_custom.ticket,
       ticket_custom.mn,
       ticket_custom.value,
       ticket_custom.category,
       SUM(CASE
               WHEN ticket.status IN ('new', 'assigned') THEN 1
               ELSE 0
           END) AS NEW,
       SUM(CASE
               WHEN ticket.status IN ('new', 'assigned') THEN 1
               ELSE 0
           END) AS OLD,
       SUM(CASE
               WHEN ticket.status='closed' THEN 1
               ELSE 0
           END) AS Closed,
       count(id) AS Total,
       EmployeeConsolidated.id,
       EmployeeConsolidated.rate,
       ticket.id AS _id
FROM engine.ticket
INNER JOIN engine.ticket_custom ON ticket.id = ticket_custom.ticket
LEFT JOIN
  (SELECT e.employee_id AS "Employee #" ,
          e.first_name || ' ' || e.last_name AS "Name" ,
          e.email AS "Email" ,
          e.phone_number AS "Phone" ,
          TO_CHAR(e.hire_date, 'MM/DD/YYYY') AS "Hire Date" ,
          TO_CHAR(e.salary, 'L99G999D99', 'NLS_NUMERIC_CHARACTERS = ''.,'' NLS_CURRENCY = ''$''') AS "Salary" ,
          e.commission_pct AS "Comission %" ,
          'works as ' || j.job_title || ' in ' || d.department_name || ' department (manager: ' || dm.first_name || ' ' || dm.last_name || ') and immediate supervisor: ' || m.first_name || ' ' || m.last_name AS "Current Job" ,
          TO_CHAR(j.min_salary, 'L99G999D99', 'NLS_NUMERIC_CHARACTERS = ''.,'' NLS_CURRENCY = ''$''') || ' - ' || TO_CHAR(j.max_salary, 'L99G999D99', 'NLS_NUMERIC_CHARACTERS = ''.,'' NLS_CURRENCY = ''$''') AS "Current Salary" ,
          l.street_address || ', ' || l.postal_code || ', ' || l.city || ', ' || l.state_province || ', ' || c.country_name || ' (' || r.region_name || ')' AS "Location" ,
          jh.job_id AS "History Job ID" ,
          'worked from ' || TO_CHAR(jh.start_date, 'MM/DD/YYYY') || ' to ' || TO_CHAR(jh.end_date, 'MM/DD/YYYY') || ' as ' || jj.job_title || ' in ' || dd.department_name || ' department' AS "History Job Title"
   FROM employees e -- to get title of current job_id

   JOIN jobs j ON e.job_id = j.job_id -- to get name of current manager_id

   LEFT JOIN employees m ON e.manager_id = m.employee_id -- to get name of current department_id

   LEFT JOIN departments d ON d.department_id = e.department_id -- to get name of manager of current department
-- (not equal to current manager and can be equal to the employee itself)

   LEFT JOIN employees dm ON d.manager_id = dm.employee_id -- to get name of location

   LEFT JOIN locations l ON d.location_id = l.location_id
   LEFT JOIN countries c ON l.country_id = c.country_id
   LEFT JOIN regions r ON c.region_id = r.region_id -- to get job history of employee

   LEFT JOIN job_history jh ON e.employee_id = jh.employee_id -- to get title of job history job_id

   LEFT JOIN jobs jj ON jj.job_id = jh.job_id -- to get namee of department from job history

   LEFT JOIN departments dd ON dd.department_id = jh.department_id
   ORDER BY e.employee_id) AS EmployeeConsolidated ON e.employee_id = engine.ide
WHERE ticket_custom.name='chapter'
  AND ticket_custom.value LIKE '%c%'
  AND TYPE='New material'
  AND milestone='1.1.12'
  AND component NOT LIKE 'internal_engine'
GROUP BY ticket.id


        """


sqlquery3 =                  """
SELECT '%c%' AS Chapter, 
    CASE
WHEN ACCT. type = ‘NonPersonal’ THEN ‘NonPers’
WHEN CAST(FLOOR(DATEDIFF(DAY, ACCT.birth_dt,(Select CurrentMonth from CurrentYear))/365) as Varchar(3)) < 18 THEN ‘LessThan18’
WHEN CAST(FLOOR(DATEDIFF(DAY, ACCT.birth_dt,(Select CurrentMonth from CurrentYear))/365) as Varchar(3)) BETWEEN 18 AND 29 THEN ‘18-29’
WHEN CAST(FLOOR(DATEDIFF(DAY, ACCT.birth_dt,(Select CurrentMonth from CurrentYear))/365) as Varchar(3)) BETWEEN 30 AND 39 THEN ‘30-39’
WHEN CAST(FLOOR(DATEDIFF(DAY, ACCT.birth_dt,(Select CurrentMonth from CurrentYear))/365) as Varchar(3)) BETWEEN 40 AND 49 THEN ‘40-49’
WHEN CAST(FLOOR(DATEDIFF(DAY, ACCT.birth_dt,(Select CurrentMonth from CurrentYear))/365) as Varchar(3)) BETWEEN 50 AND 59 THEN ‘50-59’
WHEN ACCT.birth_dt is null then ‘Unknown’
ELSE ‘60 plus’
END AS CurrentAgeBand,
       SUM(CASE
               WHEN ticket.status IN ('new', 'assigned') THEN 1
               ELSE 0
           END) AS OLD,
       SUM(CASE
               WHEN ticket.status='closed' THEN 1
               ELSE 0
           END) AS Closed,
       count(id) AS Total,
       EmployeeConsolidated.id,
       EmployeeConsolidated.rate,
       ticket.id AS _id
FROM engine.ticket
INNER JOIN engine.ticket_custom ON ticket.id = ticket_custom.ticket
LEFT JOIN
  (SELECT e.employee_id AS "Employee #" ,
          e.first_name || ' ' || e.last_name AS "Name" ,
          e.email AS "Email" ,
          e.phone_number AS "Phone" ,
          TO_CHAR(e.hire_date, 'MM/DD/YYYY') AS "Hire Date" ,
          TO_CHAR(e.salary, 'L99G999D99', 'NLS_NUMERIC_CHARACTERS = ''.,'' NLS_CURRENCY = ''$''') AS "Salary" ,
          e.commission_pct AS "Comission %" ,
          'works as ' || j.job_title || ' in ' || d.department_name || ' department (manager: ' || dm.first_name || ' ' || dm.last_name || ') and immediate supervisor: ' || m.first_name || ' ' || m.last_name AS "Current Job" ,
          TO_CHAR(j.min_salary, 'L99G999D99', 'NLS_NUMERIC_CHARACTERS = ''.,'' NLS_CURRENCY = ''$''') || ' - ' || TO_CHAR(j.max_salary, 'L99G999D99', 'NLS_NUMERIC_CHARACTERS = ''.,'' NLS_CURRENCY = ''$''') AS "Current Salary" ,
          l.street_address || ', ' || l.postal_code || ', ' || l.city || ', ' || l.state_province || ', ' || c.country_name || ' (' || r.region_name || ')' AS "Location" ,
          jh.job_id AS "History Job ID" ,
          'worked from ' || TO_CHAR(jh.start_date, 'MM/DD/YYYY') || ' to ' || TO_CHAR(jh.end_date, 'MM/DD/YYYY') || ' as ' || jj.job_title || ' in ' || dd.department_name || ' department' AS "History Job Title"
   FROM employees e -- to get title of current job_id

   JOIN jobs j ON e.job_id = j.job_id -- to get name of current manager_id

   LEFT JOIN employees m ON e.manager_id = m.employee_id -- to get name of current department_id

   LEFT JOIN departments d ON d.department_id = e.department_id -- to get name of manager of current department
-- (not equal to current manager and can be equal to the employee itself)

   LEFT JOIN employees dm ON d.manager_id = dm.employee_id -- to get name of location

   LEFT JOIN locations l ON d.location_id = l.location_id
   LEFT JOIN countries c ON l.country_id = c.country_id
   LEFT JOIN regions r ON c.region_id = r.region_id -- to get job history of employee

   LEFT JOIN job_history jh ON e.employee_id = jh.employee_id -- to get title of job history job_id

   LEFT JOIN jobs jj ON jj.job_id = jh.job_id -- to get namee of department from job history

   LEFT JOIN departments dd ON dd.department_id = jh.department_id
   ORDER BY e.employee_id) AS EmployeeConsolidated ON e.employee_id = engine.ide
WHERE ticket_custom.name='chapter'
  AND ticket_custom.value LIKE '%c%'
  AND TYPE='New material'
  AND milestone='1.1.12'
  AND component NOT LIKE 'internal_engine'
GROUP BY ticket.id


        """
parsedquery = Parser(sqlquery)
parsedquery2 = Parser(sqlquery2)
# f = open("Input query.csv")
# SqlScript = f.read()
# f.close()
# generalize_sql(SqlScript)
class SQLTokenVisitor:
    def visit(self, token):
        """Visit a token."""
        method = 'visit_' + type(token).__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(token)

    def generic_visit(self, token):
        """Called if no explicit visitor function exists for a node."""
        if not isinstance(token, TokenList):
            return
        for tok in token:
            self.visit(tok)

def walk_tokens(token):
    queue = deque([token])
    while queue:
        token = queue.popleft()
        if isinstance(token, TokenList):
            queue.extend(token)
        yield token

statement, = sqlparse.parse(sqlquery)
statement2, = sqlparse.parse(sqlquery2)


class CaseVisitor(SQLTokenVisitor):
    """Build a list of SQL Case nodes

      The .cases list is a list of (condition, value) tuples per CASE statement

    """
    def __init__(self):
        self.cases = []

    def visit_Case(self, token):
        branches = []
        for when, then_ in token.get_cases():
            branches
        self.cases.append(token.get_cases())

visitor = CaseVisitor()
visitor.visit(statement)
visitor2 = CaseVisitor()
visitor2.visit(statement2)
cases = visitor.cases
cases2 = visitor2.cases


def find_dic(item, key):
    if isinstance(item, dict):
        for k,v in item.items():
            key[k] = v
            find_dic(v, key)
    else:
        return item
 
def get_by_key(item, key):
    dic = {}
    find_dic(item, dic)
    value = dic.get(key)
    return value

def parseCase(query):
    splitedquery = query.split(",")
    split_list = query.split(",")
    need_join = False
    join_list = []
    for sentence in split_list:
        if need_join:
            join_list[-1] = join_list[-1] + "," + sentence
        else:
            join_list.append(sentence)
        if "case" in sentence.lower():
            need_join = True
        if "end" in sentence.lower():
            need_join = False

    caselist = []
    # for i in splitedquery :
    for i in join_list :
        if(("CASE" in i) | ("case" in i)) :
            casename = i.split(" ")[len(i.split(" "))-1]
            casedict = {'name': casename, 'statement': ' '.join(i.split())}
            caselist.append(casedict)
    print("List format case statement")
    print(caselist)
    book = xlwt.Workbook()
    sheet = book.add_sheet('sheet1')
    title = ['Name','Case statement']
    row = 0
    for t in title:
        sheet.write(0,row,t)
        row+=1

    for d in caselist:  
        col=0
        for one in d.keys():
            sheet.write(row,col,d[one]) 
            col+=1
        row+=1
    book.save('Case1.xls')


if __name__ == "__main__":
    # print("query1 case: ")
    # print(cases)
    # print("query2 case: ")
    # print(cases2)
    # print("query1 subqueries: ")
    # print(parsedquery.subqueries)
    # print("query1 comments: ")
    # print(parsedquery.comments)
    # print("query2 subqueries: ")
    # print(parsedquery2.subqueries)
    # print("query2 comments: ")
    # print(parsedquery2.comments)
#     print(parse(
#         """
# SELECT
# COUNT(resum.id) AS number,
# ( CASE WHEN DATE_FORMAT(resum.happenedTime,'%H') >'8' AND DATE_FORMAT(resum.happenedTime,'%H') <= '16' THEN '8-16'
# WHEN DATE_FORMAT(resum.happenedTime,'%H') > '16' AND DATE_FORMAT(resum.happenedTime,'%H') <= '24' THEN '16'
# WHEN DATE_FORMAT(resum.happenedTime,'%H') > '0' AND DATE_FORMAT(resum.happenedTime,'%H') <= '8' THEN '0-8'
# END) AS projectBreakdown
# FROM `naers_eventsresume` resum
# INNER JOIN sys_hospital hos ON resum.hospitalId=hos.hospital_id AND hos.status=0
# WHERE resum.STATUS=3 AND eventType=1
# AND (resum.happenedTime BETWEEN '2018-09-01' AND CONCAT('2018-09-30',' 23:59:59'))
# GROUP BY projectBreakdown;
# """
# ));
#     qqq, = sqlparse.parse(
#         """
# SELECT
# COUNT(resum.id) AS number,
# ( CASE WHEN DATE_FORMAT(resum.happenedTime,'%H') >'8' AND DATE_FORMAT(resum.happenedTime,'%H') <= '16' THEN '8-16'
# WHEN DATE_FORMAT(resum.happenedTime,'%H') > '16' AND DATE_FORMAT(resum.happenedTime,'%H') <= '24' THEN '16'
# WHEN DATE_FORMAT(resum.happenedTime,'%H') > '0' AND DATE_FORMAT(resum.happenedTime,'%H') <= '8' THEN '0-8'
# END) AS projectBreakdown
# FROM `naers_eventsresume` resum
# INNER JOIN sys_hospital hos ON resum.hospitalId=hos.hospital_id AND hos.status=0
# WHERE resum.STATUS=3 AND eventType=1
# AND (resum.happenedTime BETWEEN '2018-09-01' AND CONCAT('2018-09-30',' 23:59:59'))
# GROUP BY projectBreakdown;
# """
#     )

    # print(parse(sqlquery2)['select'][1])
    # print(get_by_key(parse(sqlquery2)['select'][1], 'case'))
    parseCase(sqlquery3)
