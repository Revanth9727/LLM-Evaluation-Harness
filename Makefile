.PHONY: setup test smoke eval regression judge-healthcheck metamorphic replay

setup:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

test:
	pytest tests/ -v

smoke:
	python -m eval_harness.run --config configs/smoke.yaml

smoke-mock:
	python -m eval_harness.run --config configs/smoke_mock.yaml

eval:
	python -m eval_harness.run --config configs/regression.yaml

regression:
	python -m eval_harness.run --config configs/regression.yaml

judge-healthcheck:
	python -m eval_harness.calibrate --config configs/judge_calibration.yaml

metamorphic:
	python -m eval_harness.metamorphic --config configs/metamorphic.yaml

replay:
	python -m eval_harness.replay --case_id $(CASE_ID) --artifact_dir $(ARTIFACT_DIR)
