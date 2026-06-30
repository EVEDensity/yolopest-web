import React from 'react'
import { Row, Col, Image, Descriptions, Tag } from 'antd'
import { HistoryRecord } from '../../../types/history'

interface ImageResultViewProps {
    record: HistoryRecord
    formatDate: (timestamp: number) => string
}

export const ImageResultView: React.FC<ImageResultViewProps> = ({
    record,
    formatDate,
}) => {
    const predictions = record.result.predictions || []

    return (
        <Row gutter={[16, 16]}>
            <Col span={24} md={12}>
                <Image
                    src={record.thumbnail}
                    alt={record.filename}
                    style={{ maxWidth: '100%' }}
                />
            </Col>
            <Col span={24} md={12}>
                <Descriptions title="检测信息" bordered column={1}>
                    <Descriptions.Item label="文件名">
                        {record.filename}
                    </Descriptions.Item>
                    <Descriptions.Item label="检测时间">
                        {formatDate(record.timestamp)}
                    </Descriptions.Item>
                    <Descriptions.Item label="检测状态">
                        <Tag
                            color={
                                record.result.status === 'success'
                                    ? 'green'
                                    : record.result.status === 'no_detection'
                                      ? 'orange'
                                      : 'red'
                            }
                        >
                            {record.result.status}
                        </Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="检测耗时">
                        {record.result.time_cost ?? 0}秒
                    </Descriptions.Item>
                    <Descriptions.Item label="检测数量">
                        {predictions.length}个目标
                    </Descriptions.Item>
                    {predictions.map((pred, idx) => (
                        <React.Fragment key={idx}>
                            <Descriptions.Item label={`目标 ${idx + 1} 类型`}>
                                {pred.class}
                            </Descriptions.Item>
                            <Descriptions.Item label={`目标 ${idx + 1} 置信度`}>
                                {(pred.confidence * 100).toFixed(2)}%
                            </Descriptions.Item>
                            <Descriptions.Item label={`目标 ${idx + 1} 坐标`}>
                                X[{pred.box[0]}-{pred.box[2]}] Y[{pred.box[1]}-
                                {pred.box[3]}]
                            </Descriptions.Item>
                        </React.Fragment>
                    ))}
                </Descriptions>
            </Col>
        </Row>
    )
}
