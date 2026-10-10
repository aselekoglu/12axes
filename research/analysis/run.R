# Research-only ordinal measurement pipeline.
# Usage: Rscript research/analysis/run.R <private_export_dir> <private_output_dir>
# Intentionally refuses to infer psychometric validity from small or synthetic samples.

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) stop("Usage: Rscript run.R PRIVATE_DATA_DIR NEW_PRIVATE_OUTPUT_DIR")
input <- normalizePath(args[[1]], mustWork = TRUE)
if (file.exists(file.path(input, "SYNTHETIC_TEST_DATA_ONLY"))) {
  warning("SYNTHETIC DEMO DATA — not actual participants or evidence of instrument validity")
}
output <- args[[2]]
if (dir.exists(output)) stop("Output directory must not already exist")
required <- c("participants.csv", "assignments.csv", "answers.csv")
if (!all(file.exists(file.path(input, required)))) stop("Required study files missing")

participants <- read.csv(file.path(input, "participants.csv"), stringsAsFactors=FALSE)
assignments <- read.csv(file.path(input, "assignments.csv"), stringsAsFactors=FALSE)
answers <- read.csv(file.path(input, "answers.csv"), stringsAsFactors=FALSE)
if (length(unique(participants$instrument_version)) != 1) stop("Mixed instrument versions")
if (!all(participants$split %in% c("efa","cfa"))) stop("Unexpected EFA/CFA allocation")
if (anyDuplicated(answers[, c("participant_id", "question_id")])) stop("Duplicate response")
if (anyDuplicated(assignments[, c("participant_id","question_id")])) stop("Duplicate assignment")
if (!all(answers$response %in% c("STRONGLY_DISAGREE","DISAGREE","NEUTRAL",
                                 "AGREE","STRONGLY_AGREE"))) stop("Invalid response code")
if (!all(paste(answers$participant_id,answers$question_id) %in%
         paste(assignments$participant_id,assignments$question_id))) stop("Unassigned answers")
if (any(duplicated(participants$participant_id))) stop("Duplicate participants")

eligible <- participants[participants$completed == 1, , drop=FALSE]
if (sum(eligible$split == "efa") < 300 || sum(eligible$split == "cfa") < 300) {
 stop("Exploratory minimum 300 per split not met; do not run factor models")
}

coverage <- aggregate(question_id ~ axis_id + agree_pole, data=assignments,
                      FUN=function(x) length(unique(x)))
if (any(coverage$question_id != 10)) stop("Unexpected axis/polarity bank coverage")
anchor <- aggregate(question_id ~ question_id, data=assignments,
                    FUN=length)
colnames(anchor) <- c("question_id","assigned_n")
expected_n <- nrow(participants)
common_ids <- anchor$question_id[anchor$assigned_n == expected_n]
if (length(common_ids) != 72) stop("Exactly 72 universal anchor items required")

scale_map <- c(STRONGLY_DISAGREE=1L, DISAGREE=2L, NEUTRAL=3L, AGREE=4L, STRONGLY_AGREE=5L)
subset <- answers[answers$question_id %in% common_ids, , drop=FALSE]
subset$value <- unname(scale_map[subset$response])
subset$value[subset$agree_pole == "RIGHT"] <- 6L - subset$value[subset$agree_pole == "RIGHT"]
wide <- reshape(subset[, c("participant_id","question_id","value")], idvar="participant_id",
                timevar="question_id", direction="wide")
names(wide) <- sub("^value\\.", "", names(wide))
cols <- setdiff(names(wide), "participant_id")
if (length(cols) != 72) stop("Incorrect anchor item count in responses")

joined <- merge(eligible[,c("participant_id","split")], wide, by="participant_id")
if (nrow(joined) != nrow(eligible) || anyNA(joined[,cols]))
  stop("Incomplete anchor responses; check response capture and planned missingness")
efa <- joined[joined$split=="efa", cols, drop=FALSE]
cfa <- joined[joined$split=="cfa", cols, drop=FALSE]
if (!requireNamespace("psych", quietly=TRUE) ||
    !requireNamespace("lavaan", quietly=TRUE)) stop("psych and lavaan must be installed")

dir.create(output, mode="0700", recursive=FALSE)
write.csv(coverage, file.path(output,"coverage.csv"), row.names=FALSE)
write.csv(data.frame(split=c("efa","cfa"), n=c(nrow(efa),nrow(cfa))),
          file.path(output,"sample_counts.csv"), row.names=FALSE)

# EFA: exploratory only; compare oblique factor solutions. Number is a hypothesis.
poly <- psych::polychoric(efa)$rho
parallel <- psych::fa.parallel(poly, n.obs=nrow(efa), fm="minres",
                             fa="fa", plot=FALSE)
capture.output(parallel, file=file.path(output,"parallel_analysis.txt"))
efa_fit <- psych::fa(poly, nfactors=12, n.obs=nrow(efa), rotate="oblimin", fm="minres")
capture.output(print(efa_fit), file=file.path(output,"efa_12_factor_exploratory.txt"))

# CFA uses **independent held-out subjects** and a preregistered fixed 12-axis model.
axis <- sub("_[0-9]+$", "", cols)
groups <- split(cols, axis)
if (length(groups) != 12 || any(lengths(groups) != 6)) stop("Anchor factor groups malformed")
model <- paste(vapply(names(groups), function(name)
  paste0(name, " =~ ", paste(groups[[name]], collapse=" + ")), ""), collapse="\n")
writeLines(model, file.path(output,"cfa_model.txt"))
cfa_fit <- lavaan::cfa(model, data=cfa, ordered=cols, estimator="WLSMV",
                       std.lv=TRUE, missing="listwise")
write.csv(as.data.frame(lavaan::fitMeasures(cfa_fit)),
          file.path(output,"cfa_fit_measures.csv"))
capture.output(summary(cfa_fit, fit.measures=TRUE, standardized=TRUE),
               file=file.path(output,"cfa_12_factor_holdout.txt"))

cat("Exploratory and confirmatory outputs written to restricted directory.\n")
cat("These do not establish validity without preregistered criteria, model alternatives,\n")
cat("external benchmarks, invariance, sensitivity, expert review, and replication.\n")
