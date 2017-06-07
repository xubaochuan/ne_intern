#coding=utf-8
import sys
import argparse
import tensorflow as tf
import numpy as np
import input_data

model_path = "trainmodel"

learning_rate = 0.001
training_iters = 200
display_step = 20

image_height = 256
image_width = 256
n_channel = 6
n_class = 2
dropout = 0.8

x = tf.placeholder(tf.float32, [None, image_height, image_width, n_channel])
y = tf.placeholder(tf.float32, [None, n_class])
keep_prob = tf.placeholder(tf.float32)

# 卷积操作
def conv2d(name, l_input, w, b):
    return tf.nn.relu(tf.nn.bias_add(tf.nn.conv2d(l_input, w, strides=[1, 1, 1, 1], padding='SAME'),b), name=name)

# 最大下采样操作
def max_pool(name, l_input, k):
    return tf.nn.max_pool(l_input, ksize=[1, k, k, 1], strides=[1, k, k, 1], padding='SAME', name=name)

# 归一化操作
def norm(name, l_input, lsize=4):
    return tf.nn.lrn(l_input, lsize, bias=1.0, alpha=0.001 / 9.0, beta=0.75, name=name)

# define the alexnet
def alex_net(_X, _weights, _biases, _dropout):
    conv1 = conv2d('conv1', _X, _weights['wc1'], _biases['bc1'])
    pool1 = max_pool('pool1', conv1, k=2)
    norm1 = norm('norm1', pool1, lsize=4)
    dropout1 = tf.nn.dropout(norm1, _dropout)

    conv2 = conv2d('conv2', dropout1, _weights['wc2'], _biases['bc2'])
    pool1 = max_pool('pool2', conv2, k=2)
    norm2 = norm('norm2', pool1, lsize=4)
    dropout2 = tf.nn.dropout(norm2, _dropout)

    conv3 = conv2d('conv3', dropout2, _weights['wc3'], _biases['bc3'])
    pool3 = max_pool('pool3', conv3, k=2)
    norm3 = norm('norm3', pool3, lsize=4)
    dropout3 = tf.nn.dropout(norm3, _dropout)

    dense1 = tf.reshape(dropout3, [-1, _weights['wd1'].get_shape()[0].value])
    dense1 = tf.nn.relu(tf.matmul(dense1, _weights['wd1']) + _biases['bd1'], name='fc1')
    dense2 = tf.nn.relu(tf.matmul(dense1, _weights['wd2']) + _biases['bd2'], name='fc2')

    out = tf.matmul(dense2, _weights['out']) + _biases['out']

    return out

def train():
    weights = {
        'wc1': tf.Variable(tf.random_normal([3, 3, 6, 64])),
        'wc2': tf.Variable(tf.random_normal([3, 3, 64, 128])),
        'wc3': tf.Variable(tf.random_normal([3, 3, 128, 256])),
        'wd1': tf.Variable(tf.random_normal([32*32*256, 1024])),
        'wd2': tf.Variable(tf.random_normal([1024, 1024])),
        'out': tf.Variable(tf.random_normal([1024, n_class]))
    }
    biases = {
        'bc1': tf.Variable(tf.random_normal([64])),
        'bc2': tf.Variable(tf.random_normal([128])),
        'bc3': tf.Variable(tf.random_normal([256])),
        'bd1': tf.Variable(tf.random_normal([1024])),
        'bd2': tf.Variable(tf.random_normal([1024])),
        'out': tf.Variable(tf.random_normal([n_class]))
    }

    #construct model

    pred = alex_net(x, weights, biases, keep_prob)

    cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(pred, y))
    optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)

    correct_pred = tf.equal(tf.argmax(pred, 1), tf.argmax(y, 1))
    accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))

    saver = tf.train.Saver()

    init = tf.initialize_all_variables()

    with tf.Session() as sess:
        sess.run(init)
        saver.restore(sess, model_path)
        step = 1
        batch_index = 0
        batch_size = 32
        iter_index = 0
        best_acc = 0
        while iter_index < training_iters:
            print "step: " + str(step)
            batch_xs, batch_ys, batch_index, iter_add = input_data.next_batch("train", batch_size, batch_index)
            iter_index += iter_add
            sess.run(optimizer, feed_dict={x: batch_xs, y: batch_ys, keep_prob: dropout})
            if step % display_step == 0:
                acc = sess.run(accuracy, feed_dict={x: batch_xs, y: batch_ys, keep_prob: 1.})
                loss = sess.run (cost, feed_dict={x: batch_xs, y: batch_ys, keep_prob: 1.})
                print "Iter " + str(iter_index) + ", Minibatch Loss= " + "{:.6f}".format(loss) + ", Training Accuracy= " + "{:.5f}".format(acc)
                if acc > best_acc:
                    saver.save(sess, model_path)
            step += 1
        print "Optimization Finished!"

def test():
    weights = {
        'wc1': tf.Variable(tf.random_normal([3, 3, 6, 64])),
        'wc2': tf.Variable(tf.random_normal([3, 3, 64, 128])),
        'wc3': tf.Variable(tf.random_normal([3, 3, 128, 256])),
        'wd1': tf.Variable(tf.random_normal([32 * 32 * 256, 1024])),
        'wd2': tf.Variable(tf.random_normal([1024, 1024])),
        'out': tf.Variable(tf.random_normal([1024, n_class]))
    }
    biases = {
        'bc1': tf.Variable(tf.random_normal([64])),
        'bc2': tf.Variable(tf.random_normal([128])),
        'bc3': tf.Variable(tf.random_normal([256])),
        'bd1': tf.Variable(tf.random_normal([1024])),
        'bd2': tf.Variable(tf.random_normal([1024])),
        'out': tf.Variable(tf.random_normal([n_class]))
    }
    pred = alex_net(x, weights, biases, keep_prob)

    correct_pred = tf.equal(tf.argmax(pred, 1), tf.argmax(y, 1))
    accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))

    saver = tf.train.Saver()
    init = tf.initialize_all_variables()

    with tf.Session() as sess:
        sess.run(init)
        saver.restore(sess, model_path)
        batch_index = 0
        batch_size = 100
        iter_add = 0
        while iter_add == 0:
            print batch_index
            batch_xs, batch_ys, batch_index, iter_add = input_data.next_batch("test", batch_size, batch_index)
            acc = sess.run(accuracy, feed_dict={x: batch_xs, y: batch_ys, keep_prob: 1.})
            print "Test Accuracy= " + "{:.5f}".format(acc)

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
    )
    args = parser.parse_args()

    if args.mode == 'train':
        train()
    else:
        test()

if __name__=='__main__':
    main(sys.argv);
