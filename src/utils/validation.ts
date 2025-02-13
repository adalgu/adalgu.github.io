import { PageObjectResponse } from "@notionhq/client/build/src/api-endpoints";

export interface ValidationError {
  property: string;
  message: string;
}

export const validationRules = {
  Author: {
    required: false,
    validate: (value: any): boolean =>
      value?.type === "rich_text" && Array.isArray(value.rich_text),
  },
  ShowToc: {
    required: false,
    validate: (value: any): boolean =>
      value?.type === "checkbox" && typeof value.checkbox === "boolean",
  },
  Tags: {
    required: false,
    validate: (value: any): boolean =>
      value?.type === "multi_select" && Array.isArray(value.multi_select),
  },
};

export function validateRequiredProperties(
  page: PageObjectResponse,
): ValidationError[] {
  const errors: ValidationError[] = [];
  const required = [
    "Name",
    "isPublished",
    "Description",
    "Tags",
    "Created time",
    "Last Updated",
  ];

  for (const prop of required) {
    if (!page.properties[prop]) {
      errors.push({
        property: prop,
        message: `Missing required property: ${prop}`,
      });
    }
  }

  return errors;
}

export function validateOptionalProperties(
  page: PageObjectResponse,
): ValidationError[] {
  const errors: ValidationError[] = [];

  for (const [property, rule] of Object.entries(validationRules)) {
    if (page.properties[property]) {
      const value = page.properties[property];
      if (!rule.validate(value)) {
        errors.push({
          property,
          message: `Invalid value for optional property: ${property}`,
        });
      }
    }
  }

  return errors;
}

export function validatePage(page: PageObjectResponse): ValidationError[] {
  return [
    ...validateRequiredProperties(page),
    ...validateOptionalProperties(page),
  ];
}
