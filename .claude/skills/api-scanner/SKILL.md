---
name: api-scanner
description: Scans REST controllers, form controllers
             and request/response objects in repo/ to
             find where the attribute enters or exits
             the application boundary via APIs or forms.
             Use when tracing attribute at the API layer.
---

When scanning the API layer for an attribute:

1. Search repo/src/main/java for:
   - @RestController classes
   - @Controller classes (MVC/Thymeleaf)
   - @RequestMapping, @GetMapping, @PostMapping,
     @PutMapping, @DeleteMapping methods
   - @RequestBody parameter classes
   - @ModelAttribute usage
   - Thymeleaf templates in resources/templates/
     (look for th:field or th:value with attribute)

2. For each endpoint find:
   - HTTP method (GET/POST/PUT/DELETE)
   - URL path
   - Whether attribute comes IN or goes OUT:
     INBOUND:  POST/PUT body, @RequestParam, @PathVariable
     OUTBOUND: response body, Model attribute, JSON response
   - Which service or repository is called next

3. Also check:
   - OpenAPI / Swagger annotations if present
   - Any request/response DTO classes
   - Any validation annotations (@NotNull, @Email etc.)

4. Output exactly as:

   ==========================================
   API SCAN RESULT
   ==========================================
   ENDPOINT:   <HTTP METHOD> <URL path>
   DIRECTION:  INBOUND | OUTBOUND
   ATTRIBUTE:  <how attribute appears here>
   NEXT HOP:   <which class/method is called next>
   VALIDATION: <any validation rules on attribute>
   ------------------------------------------
   (repeat for each endpoint)
   ==========================================