-- Override dbt's default schema name generation so that models land in the
-- exact schema specified in dbt_project.yml (e.g. "conformed") rather than
-- "<target_schema>_<custom_schema>" (e.g. "dbt_default_conformed").
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
