from src.data_structures import InstanceType

info_1 = InstanceType(name="test_1", description="test_2", region="test_2")
info_2 = InstanceType(name="test_2", description="test_2", region="test_2")

print(info_1 == info_2)
