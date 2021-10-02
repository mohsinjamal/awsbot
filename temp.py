from awsfunc import AwsApi
import sqlite3
import time



def start():
    keyid = ''
    secret = ''

    aApi = AwsApi(keyid, secret)

    aApi.get_service_quota()
    if not aApi.get_describe_regions():
        print('获取地区列表失败， 无法进行开机')
        return False
    print(aApi.region_text)
    _region = input('请选择需要开机的区域， 例如： us-east-1 : ') or 'us-east-1'
    _region = _region.strip()
    if _region not in aApi.region_list:
        print(f'该账号不支持 {_region} 区域, 请选择重新操作。')
        return False

    _type = input('请选择需要的平台 ARM 或者 X86, 默认X86 : ') or 'X86'

    _type = _type.lower()

    instance_type = input('请输入需要创建的实例类型：默认 t2.micro  : ') or 't2.micro'

    instance_type = instance_type.strip()

    disk_size = input('请输入磁盘大小， 默认 8 : ') or '8'

    disk_size = int(disk_size)
    aApi.region = _region
    aApi.start()
    if not aApi.ec2_create_instances(instance_type, disk_size=disk_size, _type=_type):
        print('创建失败')
        return False

    print('========实例创建成功=========')
    for num in range(20):
        print(f'第 {num + 1} 次 更新实例状态')
        if aApi.get_instance(aApi.instance_id): break
        time.sleep(5)

    print('========实例信息如下=========')
    print(f'实例ID: {aApi.instance_id}, 实例IP: {aApi.ip}, 实例地区: {_region}({regions.get(_region)}), 机器平台: {_type}')
    return True


if __name__ == '__main__':
    start()

