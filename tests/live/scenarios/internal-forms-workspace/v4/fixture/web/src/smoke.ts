import * as contracts from "@orbyss-io/forms-contracts";
import * as runtime from "@orbyss-io/forms-jsonforms-runtime";
import * as reactRenderer from "@orbyss-io/forms-react";
import * as registry from "@orbyss-io/forms-renderer-registry";
import { JsonForms } from "@jsonforms/react";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

const modules = [contracts, runtime, reactRenderer, registry];
if (modules.some((value) => typeof value !== "object")) {
  throw new Error("A selected Forms module did not load.");
}
if (typeof JsonForms !== "function") {
  throw new Error("The JSON Forms React peer did not load.");
}
const markup = renderToStaticMarkup(React.createElement("div", null, "Internal Forms"));
if (markup !== "<div>Internal Forms</div>") {
  throw new Error(`Unexpected React composition output: ${markup}`);
}
console.log("Internal Forms package composition passed.");
