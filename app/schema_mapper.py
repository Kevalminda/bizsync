import re
from rapidfuzz import fuzz


# ============================================================
# CONCEPT GROUPS
# ============================================================

CONCEPT_GROUPS = {
    "customer": {
        "customer",
        "customers",
        "client",
        "clients",
        "buyer",
        "buyers",
        "purchaser",
        "cust",
        "custmer",
        "custmr",
    },

    "order": {
        "order",
        "orders",
        "ord",
        "ordr",
        "orderid",
        "order_id",
        "order_number",
        "ordernumber",
        "order_no",
        "orderno",
        "transaction",
        "transactionid",
        "transaction_id",
        "transaction_number",
        "transactionnumber",
        "txn",
    },

    "invoice": {
        "invoice",
        "invoices",
        "invoiceid",
        "invoice_id",
        "invoice_number",
        "invoicenumber",
        "invoice_no",
        "invoiceno",
        "bill",
        "billid",
        "bill_id",
        "bill_number",
        "billnumber",
    },

    "sku": {
        "sku",
        "skuid",
        "sku_id",
        "itemcode",
        "item_code",
        "productcode",
        "product_code",
        "productid",
        "product_id",
        "itemid",
        "item_id",
    },

    "product": {
        "product",
        "products",
        "item",
        "items",
        "goods",
        "material",
        "productname",
        "product_name",
        "itemname",
        "item_name",
        "description",
        "desc",
        "itemdescription",
        "item_description",
        "productdescription",
        "product_description",
        "descripshun",
    },

    "name": {
        "name",
        "title",
        "nm",
        "nme",
    },

    "quantity": {
        "quantity",
        "qty",
        "qnty",
        "quant",
        "quantty",
        "quantit",
        "units",
        "unit",
        "unitssold",
        "units_sold",
        "qtysold",
        "qty_sold",
        "count",
        "pieces",
        "piece",
        "pcs",
    },

    "amount": {
        "amount",
        "amnt",
        "amt",
        "amntt",
        "total",
        "totalamount",
        "total_amount",
        "netamount",
        "net_amount",
        "grossamount",
        "gross_amount",
        "price",
        "value",
        "revenue",
        "sales",
        "saleamount",
        "sale_amount",
        "finalamount",
        "final_amount",
        "netvalue",
        "grossvalue",
    },

    "date": {
        "date",
        "dt",
        "day",
        "orderdate",
        "order_date",
        "orderedon",
        "ordered_on",
        "saledate",
        "sale_date",
        "saleday",
        "sale_day",
        "purchase_date",
        "purchasedate",
        "transactiondate",
        "transaction_date",
        "createdat",
        "created_at",
        "updatedat",
        "updated_at",
    },

    "warehouse": {
        "warehouse",
        "warehouses",
        "location",
        "store",
        "branch",
        "site",
        "outlet",
        "depot",
    },

    "stock": {
        "stock",
        "inventory",
        "availablestock",
        "available_stock",
        "currentstock",
        "current_stock",
        "balance",
        "stocklevel",
        "stock_level",
    },

    "status": {
        "status",
        "state",
        "orderstatus",
        "order_status",
        "paymentstatus",
        "payment_status",
        "deliverystatus",
        "delivery_status",
    },

    "phone": {
        "phone",
        "mobile",
        "telephone",
        "tel",
        "contact",
        "contactnumber",
        "contact_number",
        "phonenumber",
        "phone_number",
    },

    "email": {
        "email",
        "mail",
        "emailaddress",
        "email_address",
    },
}


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_field_name(value: str) -> str:
    """
    Normalize capitalization, punctuation and separators.

    Examples:

        Customer Name  -> customer_name
        CUSTOMER-NAME  -> customer_name
        customer name  -> customer_name
        custmer name   -> custmer_name
    """

    value = str(value).strip().lower()

    value = value.replace("'", "")

    value = re.sub(
        r"[^a-z0-9]+",
        "_",
        value,
    )

    value = re.sub(
        r"_+",
        "_",
        value,
    )

    return value.strip("_")


# ============================================================
# COMPACT FORM
# ============================================================

def compact(value: str) -> str:
    """
    Remove separators.

    customer_name -> customername
    customer-name -> customername
    """

    return normalize_field_name(value).replace(
        "_",
        "",
    )


# ============================================================
# TOKENS
# ============================================================

def tokenize(value: str) -> list[str]:

    normalized = normalize_field_name(
        value
    )

    if not normalized:
        return []

    return [
        token
        for token in normalized.split("_")
        if token
    ]


# ============================================================
# CONCEPT DETECTION
# ============================================================

def detect_concepts(
    value: str,
) -> set[str]:
    """
    Identify semantic concepts represented
    by a field.

    Example:

        client_name
            -> customer
            -> name

        sale_day
            -> date
    """

    tokens = tokenize(
        value
    )

    concepts = set()

    for token in tokens:

        token_compact = (
            token.replace(
                "_",
                "",
            )
        )

        for concept, aliases in CONCEPT_GROUPS.items():

            normalized_aliases = {
                compact(alias)
                for alias in aliases
            }

            if token_compact in normalized_aliases:

                concepts.add(
                    concept
                )

    # Check the whole field as well.
    whole_value = compact(
        value
    )

    for concept, aliases in CONCEPT_GROUPS.items():

        normalized_aliases = {
            compact(alias)
            for alias in aliases
        }

        if whole_value in normalized_aliases:

            concepts.add(
                concept
            )

    return concepts


# ============================================================
# EXACT NORMALIZED MATCH
# ============================================================

def exact_match(
    source: str,
    target: str,
) -> bool:

    return (
        compact(source)
        ==
        compact(target)
    )


# ============================================================
# CONCEPT MATCH
# ============================================================

def concept_match_score(
    source: str,
    target: str,
) -> float:

    source_concepts = detect_concepts(
        source
    )

    target_concepts = detect_concepts(
        target
    )

    if not source_concepts:
        return 0.0

    if not target_concepts:
        return 0.0

    intersection = (
        source_concepts
        &
        target_concepts
    )

    if not intersection:
        return 0.0

    # Full concept match.
    if (
        source_concepts ==
        target_concepts
    ):
        return 1.0

    return 0.85


# ============================================================
# TOKEN FUZZY MATCH
# ============================================================

def token_fuzzy_score(
    source: str,
    target: str,
) -> float:

    source_tokens = [
        compact(token)
        for token in tokenize(source)
    ]

    target_tokens = [
        compact(token)
        for token in tokenize(target)
    ]

    if not source_tokens:
        return 0.0

    if not target_tokens:
        return 0.0

    best_scores = []

    for source_token in source_tokens:

        best = 0.0

        for target_token in target_tokens:

            score = (
                fuzz.ratio(
                    source_token,
                    target_token,
                )
                / 100.0
            )

            best = max(
                best,
                score,
            )

        best_scores.append(
            best
        )

    return sum(
        best_scores
    ) / len(best_scores)


# ============================================================
# WHOLE FIELD FUZZY SCORE
# ============================================================

def whole_fuzzy_score(
    source: str,
    target: str,
) -> float:

    source_value = compact(
        source
    )

    target_value = compact(
        target
    )

    if not source_value:
        return 0.0

    if not target_value:
        return 0.0

    return (
        fuzz.ratio(
            source_value,
            target_value,
        )
        / 100.0
    )


# ============================================================
# PARTIAL MATCH
# ============================================================

def partial_score(
    source: str,
    target: str,
) -> float:

    source_value = compact(
        source
    )

    target_value = compact(
        target
    )

    if not source_value:
        return 0.0

    if not target_value:
        return 0.0

    return (
        fuzz.partial_ratio(
            source_value,
            target_value,
        )
        / 100.0
    )


# ============================================================
# SPECIAL SEMANTIC RULES
# ============================================================

def semantic_rule_score(
    source: str,
    target: str,
) -> float:

    source_compact = compact(
        source
    )

    target_compact = compact(
        target
    )

    # --------------------------------------------------------
    # Date-related words
    # --------------------------------------------------------

    date_words = {
        "date",
        "day",
        "dt",
        "sale",
        "purchase",
        "ordered",
        "transaction",
        "created",
        "updated",
    }

    source_tokens = set(
        tokenize(source)
    )

    target_tokens = set(
        tokenize(target)
    )

    source_date_words = (
        source_tokens &
        date_words
    )

    target_date_words = (
        target_tokens &
        date_words
    )

    if (
        source_date_words
        and
        "date" in target_tokens
    ):
        return 0.95

    if (
        "date" in target_tokens
        and
        "day" in source_tokens
    ):
        return 0.95

    # --------------------------------------------------------
    # Amount-related words
    # --------------------------------------------------------

    amount_words = {
        "amount",
        "amt",
        "amnt",
        "total",
        "value",
        "price",
        "revenue",
        "sales",
        "net",
        "gross",
        "final",
    }

    source_amount_words = (
        source_tokens &
        amount_words
    )

    target_amount_words = (
        target_tokens &
        amount_words
    )

    if (
        source_amount_words
        and
        target_amount_words
    ):
        return 0.95

    # --------------------------------------------------------
    # Quantity-related words
    # --------------------------------------------------------

    quantity_words = {
        "quantity",
        "qty",
        "qnty",
        "quantty",
        "units",
        "pieces",
        "pcs",
        "count",
        "sold",
    }

    source_quantity_words = (
        source_tokens &
        quantity_words
    )

    target_quantity_words = (
        target_tokens &
        quantity_words
    )

    if (
        source_quantity_words
        and
        target_quantity_words
    ):
        return 0.95

    return 0.0


# ============================================================
# FINAL SCORE
# ============================================================

def calculate_score(
    source: str,
    target: str,
) -> float:

    # --------------------------------------------------------
    # Exact match gets maximum confidence.
    # --------------------------------------------------------

    if exact_match(
        source,
        target,
    ):
        return 1.0

    concept_score = concept_match_score(
        source,
        target,
    )

    semantic_score = semantic_rule_score(
        source,
        target,
    )

    token_score = token_fuzzy_score(
        source,
        target,
    )

    whole_score = whole_fuzzy_score(
        source,
        target,
    )

    partial = partial_score(
        source,
        target,
    )

    # --------------------------------------------------------
    # Strong semantic evidence should dominate.
    # --------------------------------------------------------

    if semantic_score >= 0.95:

        score = max(
            semantic_score,
            (
                concept_score * 0.35
                +
                token_score * 0.30
                +
                whole_score * 0.20
                +
                partial * 0.15
            ),
        )

    elif concept_score >= 0.85:

        score = (
            concept_score * 0.55
            +
            token_score * 0.20
            +
            whole_score * 0.15
            +
            partial * 0.10
        )

    else:

        score = (
            token_score * 0.40
            +
            whole_score * 0.35
            +
            partial * 0.25
        )

    return round(
        min(score, 1.0),
        4,
    )


# ============================================================
# CONFIDENCE
# ============================================================

def confidence_label(
    score: float,
) -> str:

    if score >= 0.85:
        return "HIGH"

    if score >= 0.65:
        return "MEDIUM"

    if score >= 0.45:
        return "LOW"

    return "VERY LOW"


# ============================================================
# FIND BEST MATCH
# ============================================================

def find_best_match(
    target_field: str,
    source_columns: list[str],
    used_sources: set[str] | None = None,
):

    if used_sources is None:
        used_sources = set()

    candidates = []

    for source in source_columns:

        if source in used_sources:
            continue

        score = calculate_score(
            source,
            target_field,
        )

        candidates.append(
            {
                "source": source,
                "score": score,
            }
        )

    if not candidates:

        return None, 0.0

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    best = candidates[0]

    return (
        best["source"],
        best["score"],
    )


# ============================================================
# SUGGEST MAPPINGS
# ============================================================

def suggest_mappings(
    target_fields: list[str],
    source_columns: list[str],
):

    suggestions = {}

    used_sources = set()

    for target in target_fields:

        source, score = find_best_match(
            target,
            source_columns,
            used_sources,
        )

        if (
            source is not None
            and
            score >= 0.45
        ):

            used_sources.add(
                source
            )

        suggestions[target] = {

            "source": source,

            "score": score,

            "confidence":
                confidence_label(
                    score
                ),
        }

    return suggestions